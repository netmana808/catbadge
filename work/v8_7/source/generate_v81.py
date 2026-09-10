#!/usr/bin/env python3
"""PLA+ V8.1 prototype: four replaceable split snap pins and sliding latch cover."""
from pathlib import Path
import sys,json,math
import numpy as np
import trimesh
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union
from shapely import affinity
import generate_v75 as old
v=old.v;b=old.b;ROOT=Path(__file__).resolve().parent.parent
P=dict(material='PLA+; formulation and printed fatigue properties unknown',roof_top=12.8,roof_bottom=11.2,
       rear_floor=1.6,rear_clearance=8.,cover_wall=1.2,cover_outer=-17.9,
       pin_slot=[4.,2.8],pin_thickness=2.4,pin_head_top=12.6,pin_hook_top=-9.8,pin_tip=-11.,
       hook_half_trials=[2.15,2.30,2.40],selected_hook_half=2.30,pin_root_z=10.5,
       pin_nominal_deflection=.35,latch_deflection=1.0,cover_slide=3.2,
       status='Unprinted prototype. Split pins and latch require PLA+ fit/cycle testing.')
P['screen_aperture']={'width':52.5,'height':40.,'left':-26.04,'right':26.46,'bottom':-27.99,'top':12.01,'right_edge_reduction_from_v8':8.5}
old.P['button_face_z']=P['roof_top']+.5
AXES=[(x+(2 if x<0 else -2),y) if i<2 else (x,y+2) for i,(x,y) in enumerate(v.D['lugs'])]
POSTS=unary_union([v.circle(x,y,3.5) for x,y in AXES])
OUTLINE=unary_union([v.D['pcb'].buffer(2.8,quad_segs=24),POSTS]).buffer(.8,quad_segs=12).buffer(-.8,quad_segs=12)
SLOTS=unary_union([box(x-2,y-1.4,x+2,y+1.4) for x,y in AXES])
# A bottom thumb latch sits entirely outside the measured battery envelope.
BEAM=Polygon([(-19.,-45.1),(14.,-44.9),(14.,-43.9),(-19.,-43.7)])
ROOT_BRIDGE=box(-21.1,-45.1,-17.8,-40.8)
BEAM_ROOT=unary_union([BEAM,ROOT_BRIDGE]).buffer(.7,quad_segs=24).buffer(-.7,quad_segs=24)
TOOTH=Polygon([(10.8,-44.9),(12.,-45.5),(14.,-45.5),(14.,-44.7)])
GUARDS=unary_union([box(-22.1,-47.3,-20.7,-40.8),box(17.8,-47.3,19.2,-40.8),
                   box(-22.1,-47.3,6.,-46.1),box(17.8,-47.3,19.2,-46.1)])
STRIKE=unary_union([box(14.3,-46.,16.3,-44.85),box(15.1,-47.,33.,-45.7),box(31.5,-47.,33.,-40.8)])
# Remove old battery screw mount; this region lies below the original PCB outline.
OLD_COVER_POST_REGION=box(-6.,-53.,6.,-42.3)

def solid(layers):return old.solid([(a,c,p) for a,c,p in layers if not p.is_empty and c-a>1e-7])
def extrude_xz(poly,thickness):
 m=solid([(0,thickness,poly)])
 matrix=np.array([[1,0,0,0],[0,0,-1,thickness/2],[0,1,0,0],[0,0,0,1.]])
 m.apply_transform(matrix);return old.stable(m)
def head_cutter(x,y):
 poly=Polygon([(-2,11.8),(2,11.8),(3.1,12.9),(-3.1,12.9)])
 m=extrude_xz(poly,2.8);m.apply_translation([x,y,0]);return m

def lid_layers(spring=True):
 out=[]
 for a,c,p in old.lid_layers(spring):
  if a>=P['roof_top']:continue
  c=min(c,P['roof_top'])
  # Fill obsolete bores only inside new smaller towers; discard old projecting lugs.
  p=unary_union([p,POSTS]).intersection(OUTLINE).difference(SLOTS)
  out.append((a,c,p))
 return out

def lid_mesh(spring=True):
 mesh=solid(lid_layers(spring))
 return old.stable(trimesh.boolean.difference([mesh]+[head_cutter(x,y) for x,y in AXES],engine='manifold'))

def rear_layers():
 out=[]
 for a,c,p in old.rear_layers():
  p=unary_union([p,POSTS.difference(v.D['pcb'].buffer(.4))]).intersection(OUTLINE.union(old.antenna.PANEL)).difference(SLOTS)
  p=p.difference(OLD_COVER_POST_REGION).difference(box(10.2,-46.,18.,-43.2).difference(STRIKE))
  # Latch strike built straight up from the tray exterior, no hanging hook.
  if a < -6.8:p=unary_union([p,STRIKE])
  out.append((a,c,p))
 # Split strike termination exactly at -6.8.
 result=[]
 for a,c,p in out:
  if a < -6.8 < c:
   result.extend([(a,-6.8,p),(-6.8,c,p.difference(STRIKE.difference(OUTLINE)))])
  else:result.append((a,c,p))
 return result

def cover_layers():
 out=[]
 for a,c,p in b.cover_layers():
  if c<=P['cover_outer']:continue
  a=max(a,P['cover_outer'])
  p=p.difference(b.POST).difference(OLD_COVER_POST_REGION)
  # Main panel and existing two retaining tabs are retained.
  out.append((a,c,p))
 # Full-height latch is connected only at its left root so it bends in XY.
 # Separate intervals avoid overlapping solids in the layered volume calculation.
 zs=sorted(set([a for a,_,_ in out]+[c for _,c,_ in out]+[-8.7]))
 result=[]
 for a,c in zip(zs,zs[1:]):
  z=(a+c)/2;p=next((p for aa,cc,p in out if aa<=z<cc),Polygon())
  if z < b.BACK:p=unary_union([p,BEAM_ROOT])
  if z < -8.7:p=unary_union([p,TOOTH])
  if z < b.BACK:p=unary_union([p,GUARDS])
  result.append((a,c,p))
 return result

def pin_mesh(half):
 # Head seats on 45-degree ramps, eliminating the old counterbore's horizontal ledge.
 head=Polygon([(-1.6,11.4),(1.6,11.4),(2.8,12.6),(-2.8,12.6)])
 body=Polygon([(-1.8,11.5),(1.8,11.5),(1.65,-9.8),(half,-9.8),(1.65,-11.),
               (-1.65,-11.),(-half,-9.8),(-1.65,-9.8)])
 slit=unary_union([Polygon([(-.65,-12),(.65,-12),(.7,10.5),(-.7,10.5)]),Point(0,10.5).buffer(.7,quad_segs=24)])
 return extrude_xz(unary_union([head,body]).difference(slit),P['pin_thickness'])

def compressed_pin(mesh,delta):
 m=mesh.copy();z=m.vertices[:,2];t=np.clip((P['pin_root_z']-z)/(P['pin_root_z']-P['pin_hook_top']),0,1)
 f=(3*t*t-t*t*t)/2
 m.vertices[:,0]-=np.sign(m.vertices[:,0])*delta*f
 return m

def deflected_cover(mesh,delta):
 m=mesh.copy();x,y,z=m.vertices.T
 # Actual moving latch, rigid guard excluded. Root bridge remains stationary.
 mask=(x>-17.8)&(x<14.001)&(y>-45.501)&(y<-43.699)
 t=np.clip((x+17.8)/31.8,0,1)
 m.vertices[mask,1]+=delta*((3*t[mask]**2-t[mask]**3)/2)
 return m

def export(name,m,orientation='up',folder='parts'):
 m=old.stable(m);m.export(ROOT/'preview'/(name+'_ASSEMBLY.stl'))
 pr=m.copy()
 if orientation=='flat_pin':pr.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/2,[1,0,0]))
 elif orientation=='down':pr.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
 pr.apply_translation(-pr.bounds[0]);pr=old.stable(pr)
 pr.export(ROOT/folder/(name+'.stl'));old.export_3mf({name:pr},ROOT/folder/(name+'.3mf'))
 print('Export',name,flush=True);return pr

def main(coupons=False):
 prints={};kit={};layouts={}
 for half in P['hook_half_trials']:
  name='snap_pin_'+str(round(half*2,2)).replace('.','p')
  prints[name]=export(name,pin_mesh(half),'flat_pin')
  kit[name]=prints[name]
 # Side tower coupon reproduces both full-depth halves and the tapered head seat.
 x,y=AXES[0];region=box(x-4.5,y-4.5,x+4.5,y+4.5)
 lc=solid([(a,c,p.intersection(region)) for a,c,p in lid_layers()])
 lc=old.stable(trimesh.boolean.difference([lc,head_cutter(x,y)],engine='manifold'))
 kit['PRINT_FIRST_pin_lid']=export('PRINT_FIRST_pin_lid',lc,'down','tests')
 rc=solid([(a,c,p.intersection(region)) for a,c,p in rear_layers()])
 kit['PRINT_FIRST_pin_tray']=export('PRINT_FIRST_pin_tray',rc,'up','tests')
 # Latch coupon is the actual bottom strip, including both protective guards.
 region=box(-23,-48,36,-38)
 for name,ls,orient in [('PRINT_FIRST_latch_cover',cover_layers(),'up'),('PRINT_FIRST_latch_tray',rear_layers(),'up')]:
  kit[name]=export(name,solid([(a,c,p.intersection(region)) for a,c,p in ls]),orient,'tests')
 for name,region in [('PRINT_FIRST_front_buttons',box(-78,-18,-33,18)),('PRINT_FIRST_right_ear_SAO',box(27,15,70,46))]:
  mesh=solid([(a,c,p.intersection(region)) for a,c,p in lid_layers()])
  cutters=[head_cutter(x,y) for x,y in AXES if region.contains(Point(x,y))]
  if cutters:mesh=old.stable(trimesh.boolean.difference([mesh]+cutters,engine='manifold'))
  kit[name]=export(name,mesh,'down','tests')
 for dia in old.P['socket_trials']:
  name=f'cap_socket_{dia:.1f}'.replace('.','p');prints[name]=export(name,old.cap_mesh(dia),'down');kit[name]=prints[name]
 kit['PRINT_FIRST_screen_52p5x40']=export('PRINT_FIRST_screen_52p5x40',solid([(P['roof_bottom'],P['roof_top'],v.screen_hole().buffer(3.,quad_segs=24).difference(v.screen_hole()))]),'down','tests')
 layouts['coupons']=old.write_kit('PRINT_FIRST_v8.1_PLA_Snaps',kit)
 if not coupons:
  for name,spring in [('faceplate',True),('faceplate_NO_SPRING_ONLY',False)]:prints[name]=export(name,lid_mesh(spring),'down')
  blank=solid(rear_layers());prints['rear_tray']=old.cut_port('rear_tray',blank)
  prints['battery_cover']=export('battery_cover',solid(cover_layers()))
  for spring in [True,False]:
   face='faceplate' if spring else 'faceplate_NO_SPRING_ONLY'
   full={face:prints[face],'rear_tray':prints['rear_tray'],'battery_cover':prints['battery_cover']}
   for i in range(4):full[f'case_snap_pin_{i+1}_TRIAL_4p6']=prints['snap_pin_4p6']
   for name in v.BUTTONS:full['button_'+name+'_TRIAL_3p2']=prints['cap_socket_3p2']
   # Stable layout: two shells above one another; narrow cover next to them.
   placed={}
   for name,xy in [(face,(3,3)),('rear_tray',(3,100)),('battery_cover',(164,3))]:
    m=full[name].copy();m.apply_translation([*xy,0]);placed[name]=m
   for i,name in enumerate([n for n in full if n.startswith('button_')]):
    m=full[name].copy();m.apply_translation([3+14*i,199,0]);placed[name]=m
   for i,name in enumerate([n for n in full if n.startswith('case_snap')]):
    m=full[name].copy();m.apply_translation([96+9*i,192,0]);placed[name]=m
   filename='CatBadge-v8.1-COMBINED-PLA-SNAP'+('' if spring else '-NO-SPRING-ONLY')
   old.export_3mf(placed,ROOT/(filename+'.3mf'));layouts[filename]=list(placed)
  solid([(0,1.6,v.D['pcb_reference'])]).export(ROOT/'preview/pcb_REFERENCE_ASSEMBLY.stl')
 (ROOT/'parameters.json').write_text(json.dumps({**P,'pin_axes':AXES,'inherited_button_parameters':old.P,'ear_parameters':old.ears.data()},indent=2))
 (ROOT/'layouts.json').write_text(json.dumps(layouts,indent=2))
 print('BUILD COMPLETE',flush=True)
if __name__=='__main__':main('--coupons' in sys.argv)
