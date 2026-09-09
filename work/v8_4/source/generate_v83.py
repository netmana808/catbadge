#!/usr/bin/env python3
"""V8.3 integral rim detents, inspired by the supplied Cynthion case.

Shallow opposed ramps permit removal by local outward wall flex. This is a
print-fit prototype; no force, strain or fatigue claim follows from the CAD.
"""
from pathlib import Path
import json,sys
import numpy as np
import trimesh
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
import generate_v81 as base
old=base.old;v=base.v;b=base.b;ROOT=base.ROOT
solid=base.solid;export=base.export;deflected_cover=base.deflected_cover
P={k:base.P[k] for k in ['material','roof_top','roof_bottom','rear_floor','rear_clearance','cover_wall','cover_outer','latch_deflection','cover_slide','screen_aperture']}
P.update(version='8.3',closure='Four integral shallow rim detents; no separate pins',
 tongue_inner=1.65,tongue_tip=-1.2,tongue_base=1.8,rim_floor=-1.4,
 rim_gap=.3,catch_width=5.,catch_overlap=.25,catch_trials=[.15,.25,.35],
 catch_peak_bottom=-.4,catch_peak_top=-.2,groove_outer=.75,
 release_deflection=.45,status='UNPRINTED PLA+ trial; physical fit, force and cycle life unverified')
PCB=v.D['pcb'];OUTLINE=PCB.buffer(2.8,quad_segs=24)
# Restore material at obsolete bores only outside the preserved PCB envelope.
FILL=old.POSTS.difference(PCB.buffer(.4,quad_segs=24))
def clean_lid(spring=True):
 return [(a,min(c,P['roof_top']),unary_union([p,FILL]).intersection(OUTLINE)) for a,c,p in base.lid_layers(spring) if a<P['roof_top']]
def clean_rear():
 out=[]
 for a,c,p in base.rear_layers():
  # Keep the independent battery-cover latch/strike and antenna panel.
  body=unary_union([p,FILL]).intersection(OUTLINE.union(old.antenna.PANEL))
  strike=p.intersection(base.STRIKE)
  out.append((a,c,unary_union([body,strike])))
 return out
COMMON=old.at(clean_lid(),1.801).intersection(old.at(clean_rear(),1.799))
TONGUE=COMMON.difference(PCB.buffer(P['tongue_inner'],quad_segs=24))
RIM_RELIEF=TONGUE.buffer(P['rim_gap'],quad_segs=24)

SNAPS=[]
for name,xy in [('left_upper',(-69,6)),('right_upper',(69,6)),('left_lower',(-56,-34.5)),('right_lower',(56,-34.5))]:
 d=PCB.exterior.project(Point(xy));c=np.array(PCB.exterior.interpolate(d).coords[0])
 t=np.array(PCB.exterior.interpolate(d+.3).coords[0])-np.array(PCB.exterior.interpolate(d-.3).coords[0]);t/=np.linalg.norm(t)
 n=np.array([t[1],-t[0]]);assert not PCB.contains(Point(c+n))
 SNAPS.append(dict(name=name,c=c,t=t,n=n))
def slab(s,t0,t1,n0,n1):
 return Polygon([s['c']+t*s['t']+n*s['n'] for t,n in [(t0,n0),(t1,n0),(t1,n1),(t0,n1)]])
CATCH_REGIONS=[slab(s,-2.5,2.5,0,4) for s in SNAPS]
GROOVE_REGIONS=[slab(s,-2.9,2.9,0,4) for s in SNAPS]
NOTCHES=unary_union([slab(s,4,7,1.25,4) for s in SNAPS])
# Exact same curved wall segment as the upper-left production joint.
COUPON_REGION=slab(SNAPS[0],-9,10,-4,5)

def lid_layers(spring=True,overlap=None):
 overlap=P['catch_overlap'] if overlap is None else overlap
 prior=clean_lid(spring);reach=P['rim_gap']+overlap
 zs=sorted(set([a for a,_,_ in prior]+[c for _,c,_ in prior]+[round(z,4) for z in np.arange(-1.2,1.801,.1)]))
 out=[]
 for a,c in zip(zs,zs[1:]):
  z=(a+c)/2
  if z>=1.8:p=old.at(prior,z)
  else:
   p=TONGUE
   # Both ramps are at 45 degrees; face-down growth is at most 0.1/0.1.
   extra=max(0.,min(reach,z-(-.4-reach),(-.2+reach)-z))
   if extra>0:
    band=COMMON.difference(PCB.buffer(P['tongue_inner']-extra,quad_segs=24))
    p=unary_union([p]+[band.intersection(r) for r in CATCH_REGIONS])
   if z<-.1:p=p.difference(NOTCHES)
  out.append((a,c,p))
 return out

def lid_mesh(spring=True,overlap=None):return solid(lid_layers(spring,overlap))
def rear_layers():
 prior=clean_rear()
 zs=sorted(set([a for a,_,_ in prior]+[c for _,c,_ in prior]+[round(z,4) for z in np.arange(-1.4,1.801,.1)]))
 out=[]
 for a,c in zip(zs,zs[1:]):
  z=(a+c)/2;p=old.at(prior,z)
  if z>=P['rim_floor']:
   p=p.difference(RIM_RELIEF)
   # Pocket starts below the catch; closing roof grows by 45 degrees upward.
   if -.9<=z<.7:
    edge=P['groove_outer']+max(0.,z-.1)
    cut=OUTLINE.difference(PCB.buffer(edge,quad_segs=24))
    p=p.difference(unary_union([cut.intersection(r) for r in GROOVE_REGIONS]))
  out.append((a,c,p))
 return out

def released_lid(mesh,delta=P['release_deflection'],indices=None):
 """Prescribed outward rim motion, not a structural/force simulation."""
 m=mesh.copy();verts=m.vertices;xy=verts[:,:2];z=verts[:,2]
 for i,s in enumerate(SNAPS):
  if indices is not None and i not in indices:continue
  rel=xy-s['c'];t=rel@s['t'];n=rel@s['n']
  along=np.clip((10-np.abs(t))/6.,0,1)
  height=np.clip((5.8-z)/5.8,0,1)
  outside=np.clip((n-.35)/.6,0,1)
  weight=along*height*outside
  verts[:,:2]+=delta*weight[:,None]*s['n']
 return m

def main(coupons=False):
 prints={};kit={};layouts={}
 # These full-height coupons preserve the actual side-wall stiffness geometry;
 # the shortened coupon's compliance still differs from the full perimeter.
 for overlap in P['catch_trials']:
  name='PRINT_FIRST_rim_lid_'+str(round(overlap,2)).replace('.','p')
  m=solid([(a,c,p.intersection(COUPON_REGION)) for a,c,p in lid_layers(overlap=overlap)])
  kit[name]=export(name,m,'down','tests')
 kit['PRINT_FIRST_rim_tray']=export('PRINT_FIRST_rim_tray',solid([(a,c,p.intersection(COUPON_REGION)) for a,c,p in rear_layers()]),'up','tests')
 region=box(-23,-48,36,-38)
 for name,ls in [('PRINT_FIRST_latch_cover',base.cover_layers()),('PRINT_FIRST_latch_tray',rear_layers())]:
  kit[name]=export(name,solid([(a,c,p.intersection(region)) for a,c,p in ls]),'up','tests')
 for name,region in [('PRINT_FIRST_front_buttons',box(-78,-18,-33,18)),('PRINT_FIRST_right_ear_SAO',box(27,15,70,46))]:
  kit[name]=export(name,solid([(a,c,p.intersection(region)) for a,c,p in lid_layers()]),'down','tests')
 for dia in old.P['socket_trials']:
  name=f'cap_socket_{dia:.1f}'.replace('.','p');prints[name]=export(name,old.cap_mesh(dia),'down');kit[name]=prints[name]
 kit['PRINT_FIRST_screen_52p5x40']=export('PRINT_FIRST_screen_52p5x40',solid([(11.2,12.8,v.screen_hole().buffer(3.,quad_segs=24).difference(v.screen_hole()))]),'down','tests')
 layouts['coupons']=old.write_kit('PRINT_FIRST_v8.3_Integral_Snaps',kit)
 if not coupons:
  for name,spring in [('faceplate',True),('faceplate_NO_SPRING_ONLY',False)]:prints[name]=export(name,lid_mesh(spring),'down')
  prints['rear_tray']=old.cut_port('rear_tray',solid(rear_layers()))
  prints['battery_cover']=export('battery_cover',solid(base.cover_layers()))
  for spring in [True,False]:
   face='faceplate' if spring else 'faceplate_NO_SPRING_ONLY';placed={}
   for name,xy in [(face,(3,3)),('rear_tray',(3,99)),('battery_cover',(158,3))]:
    m=prints[name].copy();m.apply_translation([*xy,0]);placed[name]=m
   for i,name in enumerate(v.BUTTONS):
    m=prints['cap_socket_3p2'].copy();m.apply_translation([3+14*i,199,0]);placed['button_'+name+'_TRIAL_3p2']=m
   filename='CatBadge-v8.3-COMBINED-INTEGRAL-SNAP'+('' if spring else '-NO-SPRING-ONLY')
   old.export_3mf(placed,ROOT/(filename+'.3mf'));layouts[filename]=list(placed)
  solid([(0,1.6,v.D['pcb_reference'])]).export(ROOT/'preview/pcb_REFERENCE_ASSEMBLY.stl')
 (ROOT/'parameters.json').write_text(json.dumps({**P,'snaps':[{k:val.tolist() if isinstance(val,np.ndarray) else val for k,val in s.items()} for s in SNAPS],'inherited_button_parameters':old.P,'ear_parameters':old.ears.data()},indent=2))
 (ROOT/'layouts.json').write_text(json.dumps(layouts,indent=2));print('BUILD COMPLETE',flush=True)
if __name__=='__main__':main('--coupons' in sys.argv)
