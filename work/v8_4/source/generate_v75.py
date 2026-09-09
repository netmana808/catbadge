#!/usr/bin/env python3
"""V7.5 actual CAD. PCB underside Z=0; geometry only, no printer operations."""
from pathlib import Path
import sys, json, math, io, shutil, hashlib, subprocess
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
import generate_v6 as old
import rear_antenna as antenna
import ear_panels as ears
# Restore the old inner-ear wall. The antenna now lives only in the rear tray.
old.LAND_IN=Polygon();old.LAND_OUT=Polygon()
from mesh_tools import layered_mesh, export_3mf, polygons
v=old.v; b=old.battery
ROOT=Path(__file__).resolve().parent.parent
P=dict(main_hole=4.4, main_post_radius=5.8, main_head_diameter_reference=7.6,
       main_head_height_reference=2.2, main_head_seat=13.2, main_screw_length=30,
       main_nut_AF=7.4, main_nut_depth=3.4, carrier_web=.8,
       button_face_diameter=10., button_face_z=13.7, button_socket_boss=4.8,
       socket_depth=1.5, socket_trials=[3.,3.1,3.2,3.3], guide_bore=10.6,
       guide_step_z=12., flange_diameter=11.4, flange_cavity=11.8,
       flange_bottom=9.8, flange_top=10.8, flange_chamfer_top=11.5,
       collar_bottom=9.)
P['antenna']=antenna.data()
P['ears']=ears.data()
P['button_retention']='Flanges stop outward escape while assembled; no keeper plates or M3 hardware'
POSTS=unary_union([v.circle(x,y,P['main_post_radius']) for x,y in v.D['lugs']])
# Rounded XY transitions are constant through height: no downward fillet.
OUTER=unary_union([v.D['outer'],POSTS]).buffer(2,quad_segs=16).buffer(-2,quad_segs=16)
EXTRA=OUTER.difference(v.D['outer']).intersection(POSTS.buffer(4.0))
OUTER=unary_union([v.D['outer'],EXTRA,POSTS])
GUIDES=unary_union([v.circle(*xy,P['guide_bore']/2) for xy in v.BUTTONS.values()])
CAVITIES=unary_union([v.circle(*xy,P['flange_cavity']/2) for xy in v.BUTTONS.values()])
COLLARS=unary_union([v.circle(*xy,7) for xy in v.BUTTONS.values()])
def hexagon(x,y,af):
 r=af/math.sqrt(3)
 return Polygon([(x+r*math.cos(math.radians(30+60*i)),y+r*math.sin(math.radians(30+60*i))) for i in range(6)])

def at(layers,z):
 return next(g for a,c,g in layers if a-1e-7<=z<c+1e-7)
def lid_layers(spring_access=True):
 prior=old.lid_layers()
 zs=sorted(set([a for a,_,_ in prior]+[c for _,c,_ in prior]+[P['collar_bottom'],P['guide_step_z']]+[round(z,4) for z in np.arange(9.6,11.201,.2)]))
 out=[]
 for a,c in zip(zs,zs[1:]):
  z=(a+c)/2;g=at(prior,z)
  # All four fastener tubes have a straight bore, exterior bearing face.
  g=unary_union([g,POSTS,EXTRA]).difference(v.SCREW_HOLES)
  # Remove the residual service bridge at SPI, preserving external fastener posts.
  g=g.difference(v.SPI.difference(POSTS))
  # Remove legacy collar geometry below its new start, without cutting roof/walls.
  if z<P['collar_bottom']:
   g=g.difference(old.COLLARS.difference(v.D['front']))
  else:g=unary_union([g,COLLARS])
  g=g.difference(CAVITIES if z<P['guide_step_z'] else GUIDES)
  if z>=ears.P['roof_bottom']:
   panel,openings=ears.roof(spring_access)
   g=unary_union([g,panel]).difference(openings)
  # Keep the SAO plug path open through the full faceplate wall.
  g=g.difference(ears.SAO_OPEN)
  # Taper slot relief below the roof so adjacent walls have no hanging ledge.
  if z<ears.P['roof_bottom'] and z>9.6:
   g=g.difference(ears.LED_OPEN.buffer(-(ears.P['roof_bottom']-c)))
  out.append((a,c,g))
 return out

def rear_layers():
 prior=b.rear_layers(v.SCREW_HOLES,Polygon())
 zs=sorted(set(round(z,6) for z in [a for a,_,_ in prior]+[c for _,c,_ in prior]))
 out=[]
 for a,c in zip(zs,zs[1:]):
  z=(a+c)/2
  # Extra material is outside the existing outline, leaving PCB seat untouched.
  g=unary_union([at(prior,z),POSTS.difference(v.D['pcb'].buffer(v.ORIGINAL_PARAMS['radial_clearance'])),EXTRA]).difference(v.SCREW_HOLES)
  # Main nuts bear on the flat exterior rear face, in separate open carriers.
  if z>=b.P['post_top']:g=g.difference(b.NUT)
  out.append((a,c,g))
 return antenna.revise(out)

def nut_carrier_layers(index):
 x,y=v.D['lugs'][index];disc=v.circle(x,y,7.8)
 sweep=unary_union([v.affinity.translate(unary_union([b.OUTER,b.POST]),xoff=float(dx)) for dx in np.linspace(0,3.2,17)]).buffer(.3)
 disc=disc.difference(sweep)
 pocket=hexagon(x,y,P['main_nut_AF'])
 # The front web sits BETWEEN the nut and rear tray, so tightening clamps
 # the carrier as well as both case halves. Print the flat front face down.
 # Hold the carrier while tightening; its hex pocket holds the nut against rotation.
 return [(b.BACK-P['carrier_web']-P['main_nut_depth'],b.BACK-P['carrier_web'],disc.difference(pocket)),(b.BACK-P['carrier_web'],b.BACK,disc.difference(v.SCREW_HOLES))]

def cover_layers():
 return [(a,c,unary_union([g,b.POST]).difference(b.SCREW) if (a+c)/2<b.BACK else g) for a,c,g in b.cover_layers()]

def cap_mesh(dia):
 # True 45-degree cone avoids a retaining-flange overhang. Print face down.
 tip=v.P['pcb_underside_to_unpressed_button_top'];mouth=tip-P['socket_depth']
 stem=P['button_socket_boss']/2;flange=P['flange_diameter']/2;face=P['button_face_diameter']/2
 profile=[(0,tip),(dia/2,tip),(dia/2,mouth+.2),(dia/2+.15,mouth),(stem,mouth),
          (stem,P['flange_bottom']),(flange,P['flange_bottom']),(flange,P['flange_top']),(face,P['flange_chamfer_top']),(face,P['button_face_z']),(0,P['button_face_z']),(0,tip)]
 return stable(trimesh.creation.revolve(profile,sections=128))

def stable(m):
 before=m.volume
 m=trimesh.load_mesh(io.BytesIO(m.export(file_type='stl')),file_type='stl',process=True)
 m.update_faces(m.area_faces>1e-12);m.remove_unreferenced_vertices()
 assert m.is_watertight and m.is_winding_consistent and m.volume>0 and len(m.split(only_watertight=False))==1
 assert abs(m.volume-before)<.02
 return m

def solid(ls):
 pieces=[]
 for a,c,g in ls:
  for poly in polygons(g):
   if poly.area>1e-8: pieces.append(layered_mesh([(a,c,poly)]))
 m=trimesh.boolean.union(pieces,engine='manifold') if len(pieces)>1 else pieces[0]
 expected=sum((c-a)*g.area for a,c,g in ls)
 assert abs(m.volume-expected)<.03,(m.volume,expected)
 return stable(m)

def emit(name,m,down=False,folder='parts'):
 m=stable(m);m.export(ROOT/'preview'/(name+'_ASSEMBLY.stl'))
 pr=stable(v.to_print(m,down));path=ROOT/folder/(name+'.stl');pr.export(path)
 export_3mf({name:pr},path.with_suffix('.3mf'))
 return pr

def arrange(meshes):
 # Shelf packing, 3 mm separation, nominal 220 mm square; no brim included.
 placed={};x=y=3.;row=0.
 for name,m in sorted(meshes.items(),key=lambda kv:-kv[1].extents[1]):
  w,h,_=m.extents
  if x+w>217:x=3.;y+=row+3.;row=0.
  n=m.copy();n.apply_translation([x-n.bounds[0,0],y-n.bounds[0,1],-n.bounds[0,2]])
  placed[name]=n;x+=w+3;row=max(row,h)
 return placed

def write_kit(name,meshes):
 placed=arrange(meshes)
 bound=np.vstack([m.bounds for m in placed.values()])
 assert bound[:,0].max()<=220 and bound[:,1].max()<=220,(name,bound.max(axis=0))
 export_3mf(placed,ROOT/(name+'.3mf'))
 return {k:v.extents.tolist() for k,v in placed.items()}

def cut_port(name,mesh,folder='parts'):
 blank=ROOT/'preview'/(name+'_BLANK_ASSEMBLY.stl');mesh.export(blank)
 scad=ROOT/'source'/(name+'_cut.scad');scad.write_text(antenna.cutter_scad('import("../preview/'+blank.name+'");'))
 target=ROOT/'preview'/(name+'_ASSEMBLY.stl')
 exe=shutil.which('openscad') or str(ROOT.parents[1]/'work/tools/OpenSCAD.app/Contents/MacOS/OpenSCAD')
 run=subprocess.run([exe,'-o',str(target),str(scad)],capture_output=True,text=True,timeout=180)
 (ROOT/(name+'_openscad.log')).write_text(run.stdout+run.stderr);run.check_returncode()
 return emit(name,trimesh.load_mesh(target),False,folder)

def main(coupons=False):
 prints={};layouts={};region=box(-81,-18,-33,18)
 jobs={'PRINT_FIRST_front_buttons':(solid([(a,c,g.intersection(region)) for a,c,g in lid_layers()]),True)}
 x,y=v.D['lugs'][0];disc=v.circle(x,y,5.8)
 jobs['PRINT_FIRST_M4_front_seat']=(solid([(v.JOIN,v.ROOF_TOP,disc.difference(v.SCREW_HOLES))]),True)
 jobs['PRINT_FIRST_M4_rear_seat']=(solid([(b.BACK,1.8,OUTER.intersection(v.circle(x,y,8.5)).difference(v.SCREW_HOLES))]),False)
 jobs['nut_carrier_1']=(solid(nut_carrier_layers(0)),True)
 for dia in P['socket_trials']:jobs[f'cap_socket_{dia:.1f}'.replace('.','p')]=(cap_mesh(dia),True)
 for name,(mesh,down) in jobs.items():
  print('Export',name,flush=True);prints[name]=emit(name,mesh,down,'tests' if name.startswith('PRINT') else 'parts')
 coupon=solid([(a,c,g.intersection(antenna.REGION)) for a,c,g in rear_layers()])
 prints['PRINT_FIRST_rear_antenna']=cut_port('PRINT_FIRST_rear_antenna',coupon,'tests')
 ear_region=box(27,15,70,46)
 prints['PRINT_FIRST_right_ear_SAO']=emit('PRINT_FIRST_right_ear_SAO',solid([(a,c,p.intersection(ear_region)) for a,c,p in lid_layers()]),True,'tests')
 layouts['PRINT_FIRST_v7.5_Ears_Buttons_M4']=write_kit('PRINT_FIRST_v7.5_Ears_Buttons_M4',prints)
 if not coupons:
  more={'faceplate':(solid(lid_layers()),True),'faceplate_NO_SPRING_ONLY':(solid(lid_layers(False)),True),'battery_cover':(solid(cover_layers()),False)}
  for i in range(1,4):more[f'nut_carrier_{i+1}']=(solid(nut_carrier_layers(i)),True)
  for name,(mesh,down) in more.items():
   print('Export',name,flush=True);prints[name]=emit(name,mesh,down)
  prints['rear_tray_M4']=cut_port('rear_tray_M4',solid(rear_layers()))
  kit={key:prints[key] for key in ['faceplate','rear_tray_M4','battery_cover','nut_carrier_1','nut_carrier_2','nut_carrier_3','nut_carrier_4']}
  for key in v.BUTTONS:kit['button_'+key+'_TRIAL_3p2']=prints['cap_socket_3p2']
  placed={}
  for key,xy in [('faceplate',(3,3)),('rear_tray_M4',(3,102)),('battery_cover',(169,3))]:
   mesh=kit[key].copy();mesh.apply_translation([xy[0],xy[1],0]);placed[key]=mesh
  for i,key in enumerate(v.BUTTONS):
   name='button_'+key+'_TRIAL_3p2';mesh=kit[name].copy();mesh.apply_translation([3+14*i,201,0]);placed[name]=mesh
  for i in range(4):
   name=f'nut_carrier_{i+1}';mesh=kit[name].copy();mesh.apply_translation([100+18*i,201,0]);placed[name]=mesh
  bound=np.vstack([mesh.bounds for mesh in placed.values()]);assert bound[:,0].max()<220 and bound[:,1].max()<220
  export_3mf(placed,ROOT/'CatBadge-v7.5-COMBINED-M4.3mf');layouts['combined']=list(placed)
  closed={key:mesh.copy() for key,mesh in placed.items()}
  alternate=prints['faceplate_NO_SPRING_ONLY'].copy();alternate.apply_translation([3,3,0]);del closed['faceplate'];closed['faceplate_NO_SPRING_ONLY']=alternate
  export_3mf(closed,ROOT/'CatBadge-v7.5-COMBINED-NO-SPRING-ONLY.3mf')
  layouts['combined_no_spring']=list(closed)
  solid([(0,1.6,v.D['pcb_reference'])]).export(ROOT/'preview/pcb_REFERENCE_ASSEMBLY.stl')
 (ROOT/'parameters.json').write_text(json.dumps(P,indent=2));(ROOT/'layouts.json').write_text(json.dumps(layouts,indent=2))
 print('BUILD COMPLETE',flush=True)
if __name__=='__main__':main('--coupons' in sys.argv)
