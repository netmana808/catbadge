#!/usr/bin/env python3
"""Closed-back v8.7: thicker rear panel, supported rim and wider detents."""
import json,sys
import numpy as np
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from generate_v84 import *
import generate_v84 as previous
joint=previous.prior
# Thicker tongue and wider catches; preserve board clearance and outside size.
joint.P.update(version='8.7',tongue_inner=1.4,catch_width=8.,catch_overlap=.35,
               catch_trials=[.25,.35,.45],groove_outer=.45,release_deflection=.55)
joint.TONGUE=joint.COMMON.difference(joint.PCB.buffer(joint.P['tongue_inner'],quad_segs=24))
joint.RIM_RELIEF=joint.TONGUE.buffer(joint.P['rim_gap'],quad_segs=24)
joint.CATCH_REGIONS=[joint.slab(s,-4,4,0,4) for s in joint.SNAPS]
joint.GROOVE_REGIONS=[joint.slab(s,-4.4,4.4,0,4) for s in joint.SNAPS]
joint.NOTCHES=unary_union([joint.slab(s,5,8,1.25,4) for s in joint.SNAPS])
P={**previous.P,**joint.P,'rear_floor':2.4,'rear_outer':-10.4,'cover_shift_z':-.8,
   'cover_outer':-18.7,'closure':'Four 8 mm wide integral detents and 1.4 mm tongue; physical fit unverified',
   'closed_back':'Former ear and vent windows closed; battery, UART, QWIIC and lanyard access retained'}
# Keep the original perimeter bridge under the side-access header cutouts.
HEADER_WINDOWS={n:v.D['ports'][n].intersection(PCB.buffer(-1.2,quad_segs=24)) for n in ['UART','QWIIC']}
REAR_OPEN=unary_union([v.D['battery'],*HEADER_WINDOWS.values(),v.LANYARD])
FLOOR_OUTER=unary_union([Polygon(p.exterior) for p in old.polygons(old.at(joint.clean_rear(),-8.001))]).intersection(joint.OUTLINE.union(old.antenna.PANEL))
CLOSED_PANEL=FLOOR_OUTER.difference(REAR_OPEN).difference(base.OLD_COVER_POST_REGION)
CLOSED_PANEL=CLOSED_PANEL.difference(box(10.2,-46.,18.,-43.2).difference(base.STRIKE))
COUPON_REGION=joint.slab(joint.SNAPS[0],-10,11,-4,5)

def lid_layers(spring=True,overlap=None):return previous.lid_layers(spring,overlap)
def lid_mesh(spring=True,overlap=None,region=None):return previous.lid_mesh(spring,overlap,region)
def cover_layers():return [(a-.8,c-.8,p) for a,c,p in previous.cover_layers()]
def rear_layers():
 prior=joint.rear_layers();zs=[a for a,_,_ in prior]+[c for _,c,_ in prior]
 zs+=list(np.arange(P['rear_outer'],-7.599,.1))+list(np.arange(P['rear_outer'],P['rear_outer']+.601,.05))
 zs=sorted(set(round(float(z),5) for z in zs if z>=P['rear_outer']))
 result=[];ant=old.antenna
 for a,c in zip(zs,zs[1:]):
  z=(a+c)/2
  if z < -8.:
   p=CLOSED_PANEL.difference(b.slots(z+.8))
   p=unary_union([p,ant.PANEL]).difference(ant.OUTER_CUT)
   if z>=ant.P['floor_relief_z']:p=p.difference(ant.INNER_CUT)
  else:p=old.at(prior,z)
  # Translate only the battery latch strike with the cover, retaining board datum.
  p=p.difference(base.STRIKE)
  if z < -7.6:p=unary_union([p,base.STRIKE])
  if z<P['rear_outer']+.6:
   amount=P['rear_outer']+.6-a
   cut=joint.OUTLINE.difference(joint.OUTLINE.buffer(-amount,quad_segs=24))
   p=p.difference(cut.difference(previous.finish.REAR_PROTECT))
  result.append((a,c,p))
 return result

def released_lid(mesh,delta=P['release_deflection'],indices=None):
 """Prescribed motion of the revised rim, not a material/force simulation."""
 m=mesh.copy();verts=m.vertices;xy=verts[:,:2];z=verts[:,2]
 for i,s in enumerate(SNAPS):
  if indices is not None and i not in indices:continue
  rel=xy-s['c'];t=rel@s['t'];n=rel@s['n']
  weight=np.clip((11-np.abs(t))/6.,0,1)*np.clip((5.8-z)/5.8,0,1)*np.clip((n-.3)/.3,0,1)
  verts[:,:2]+=delta*weight[:,None]*s['n']
 return m

def main(coupons=False):
 prints={};kit={};layouts={}
 # These full-height coupons preserve the actual side-wall stiffness geometry;
 # the shortened coupon's compliance still differs from the full perimeter.
 for overlap in P['catch_trials']:
  name='PRINT_FIRST_rim_lid_'+str(round(overlap,2)).replace('.','p')
  m=lid_mesh(overlap=overlap,region=COUPON_REGION)
  kit[name]=export(name,m,'down','tests')
 kit['PRINT_FIRST_rim_tray']=export('PRINT_FIRST_rim_tray',solid([(a,c,p.intersection(COUPON_REGION)) for a,c,p in rear_layers()]),'up','tests')
 region=box(-23,-48,36,-38)
 for name,ls in [('PRINT_FIRST_latch_cover',cover_layers()),('PRINT_FIRST_latch_tray',rear_layers())]:
  kit[name]=export(name,solid([(a,c,p.intersection(region)) for a,c,p in ls]),'up','tests')
 for name,region in [('PRINT_FIRST_front_buttons',box(-78,-18,-33,18)),('PRINT_FIRST_right_ear_SAO',box(27,15,70,46))]:
  kit[name]=export(name,lid_mesh(region=region),'down','tests')
 for dia in old.P['socket_trials']:
  name=f'cap_socket_{dia:.1f}'.replace('.','p');prints[name]=export(name,finish.cap_mesh(dia),'down');kit[name]=prints[name]
 kit['PRINT_FIRST_screen_52p5x40']=export('PRINT_FIRST_screen_52p5x40',solid([(11.2,12.8,v.screen_hole().buffer(3.,quad_segs=24).difference(v.screen_hole()))]),'down','tests')
 region=box(-77,-20,-62,-4)
 kit['PRINT_FIRST_cheek_grip']=export('PRINT_FIRST_cheek_grip',lid_mesh(region=region),'down','tests')
 region=box(14,-10,23,10)
 kit['PRINT_FIRST_cover_edge']=export('PRINT_FIRST_cover_edge',solid([(a,c,p.intersection(region)) for a,c,p in cover_layers()]),'up','tests')
 region=box(35,20,65,45)
 kit['PRINT_FIRST_closed_rear_ear']=export('PRINT_FIRST_closed_rear_ear',solid([(a,c,p.intersection(region)) for a,c,p in rear_layers()]),'up','tests')
 layouts['snaps']=old.write_kit('PRINT_FIRST_v8.7_Snap_Only',{n:m for n,m in kit.items() if n.startswith('PRINT_FIRST_rim_')})
 layouts['comfort']=old.write_kit('PRINT_FIRST_v8.7_Comfort_Only',{n:kit[n] for n in ['PRINT_FIRST_cheek_grip','PRINT_FIRST_cover_edge','cap_socket_3p2']})
 layouts['coupons']=old.write_kit('PRINT_FIRST_v8.7_Fit_and_Comfort',kit)
 if not coupons:
  for name,spring in [('faceplate',True),('faceplate_NO_SPRING_ONLY',False)]:prints[name]=export(name,lid_mesh(spring),'down')
  prints['rear_tray']=old.cut_port('rear_tray',solid(rear_layers()))
  prints['battery_cover']=export('battery_cover',solid(cover_layers()))
  for spring in [True,False]:
   face='faceplate' if spring else 'faceplate_NO_SPRING_ONLY';placed={}
   for name,xy in [(face,(3,3)),('rear_tray',(3,99)),('battery_cover',(158,3))]:
    m=prints[name].copy();m.apply_translation([*xy,0]);placed[name]=m
   for i,name in enumerate(v.BUTTONS):
    m=prints['cap_socket_3p2'].copy();m.apply_translation([3+14*i,199,0]);placed['button_'+name+'_TRIAL_3p2']=m
   filename='CatBadge-v8.7-COMBINED-CLOSED-BACK'+('' if spring else '-NO-SPRING-ONLY')
   old.export_3mf(placed,ROOT/(filename+'.3mf'));layouts[filename]=list(placed)
  solid([(0,1.6,v.D['pcb_reference'])]).export(ROOT/'preview/pcb_REFERENCE_ASSEMBLY.stl')
 (ROOT/'parameters.json').write_text(json.dumps({**P,'snaps':[{k:val.tolist() if isinstance(val,np.ndarray) else val for k,val in s.items()} for s in SNAPS],'inherited_button_parameters':old.P,'ear_parameters':old.ears.data()},indent=2))
 (ROOT/'layouts.json').write_text(json.dumps(layouts,indent=2));print('BUILD COMPLETE',flush=True)
if __name__=='__main__':main('--coupons' in sys.argv)
