"""Exterior-only finishing; inherited mechanical interfaces stay protected."""
import math
import numpy as np
import trimesh
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
import generate_v83 as prior
P=dict(edge_bevel=.6,button_bevel=.3,notch_bevel=.25,guard_bevel=.25,guard_corner_radius=.3,
       layer_step=.05,grip_depth=.25,grip_width=.8,grip_length=2.4,
       grip_angle=20.,grip_z=7.2,grip_y=[-16.,-13.,-10.,-7.])
# Keep all working latch geometry and its root; no cosmetic cut enters these.
COVER_PROTECT=unary_union([prior.base.BEAM_ROOT,prior.base.TOOTH]).buffer(.5)
REAR_PROTECT=unary_union([prior.old.antenna.REGION,prior.base.STRIKE.buffer(.5)])
COVER_PERIMETER_RAW=unary_union([prior.b.OUTER,prior.base.GUARDS])
COVER_PERIMETER=COVER_PERIMETER_RAW.buffer(-P['guard_corner_radius'],quad_segs=24).buffer(P['guard_corner_radius'],quad_segs=24)
GUARD_CORNERS=COVER_PERIMETER_RAW.difference(COVER_PERIMETER).intersection(prior.base.GUARDS).difference(COVER_PROTECT)

def finish_layers(layers,kind):
 edge=P['edge_bevel'];step=P['layer_step']
 start,end={'lid':(prior.P['roof_top']-edge,prior.P['roof_top']),
            'rear':(prior.b.BACK,prior.b.BACK+edge),
            'cover':(prior.P['cover_outer'],prior.P['cover_outer']+edge)}[kind]
 extra=list(np.arange(start,end+step/2,step))
 if kind=='lid':extra+=list(np.arange(-.1,-.1+P['notch_bevel']+step/2,step))
 if kind=='cover':extra+=list(np.arange(prior.b.BACK-P['guard_bevel'],prior.b.BACK+step/2,step))
 zs=sorted(set([a for a,_,_ in layers]+[c for _,c,_ in layers]+[round(float(z),5) for z in extra]))
 out=[]
 for a,c in zip(zs,zs[1:]):
  z=(a+c)/2;p=prior.old.at(layers,z)
  if start<=z<end:
   amount=c-start if kind=='lid' else end-a
   outline=prior.b.OUTER if kind=='cover' else prior.OUTLINE
   cut=outline.difference(outline.buffer(-amount,quad_segs=24))
   if kind=='rear':cut=cut.difference(REAR_PROTECT)
   elif kind=='cover':cut=cut.difference(COVER_PROTECT.union(prior.base.GUARDS.buffer(.3)))
   p=p.difference(cut)
  if kind=='cover':
   p=p.difference(GUARD_CORNERS)
   amount=max(P['guard_bevel']-(a-prior.P['cover_outer']),c-(prior.b.BACK-P['guard_bevel']),0)
   amount=min(P['guard_bevel'],amount) if z<prior.b.BACK else 0
   if amount>0:
    cut=COVER_PERIMETER.difference(COVER_PERIMETER.buffer(-amount,quad_segs=24)).intersection(prior.base.GUARDS).difference(COVER_PROTECT)
    p=p.difference(cut)
  if kind=='lid' and z<-.1+P['notch_bevel']:
   # Successively wider mouth at the outer surface, with 45-degree top entry.
   for depth in np.arange(step,P['notch_bevel']+step/2,step):
    spread=P['notch_bevel']-depth+step
    if z<-.1+spread:
     edge_band=prior.OUTLINE.difference(prior.PCB.buffer(2.8-depth,quad_segs=24))
     p=p.difference(prior.NOTCHES.buffer(spread,quad_segs=16).intersection(edge_band))
  out.append((a,c,p))
 return out

def cap_mesh(dia):
 p=prior.old.P;tip=prior.v.P['pcb_underside_to_unpressed_button_top'];mouth=tip-p['socket_depth'];face=p['button_face_diameter']/2;b=P['button_bevel'];top=p['button_face_z']
 profile=[(0,tip),(dia/2,tip),(dia/2,mouth+.2),(dia/2+.15,mouth),(p['button_socket_boss']/2,mouth),
          (p['button_socket_boss']/2,p['flange_bottom']),(p['flange_diameter']/2,p['flange_bottom']),
          (p['flange_diameter']/2,p['flange_top']),(face,p['flange_chamfer_top']),
          (face,top-b),(face-b,top),(0,top),(0,tip)]
 return prior.old.stable(trimesh.creation.revolve(profile,sections=128))

GRIPS=[]
for side in [-1,1]:
 for y in P['grip_y']:
  d=prior.PCB.exterior.project(Point(side*71,y));c=np.array(prior.PCB.exterior.interpolate(d).coords[0])
  t=np.array(prior.PCB.exterior.interpolate(d+.1).coords[0])-np.array(prior.PCB.exterior.interpolate(d-.1).coords[0]);t/=np.linalg.norm(t);n=np.array([t[1],-t[0]])
  angle=math.radians(side*P['grip_angle']);direction=np.array([math.sin(angle),math.cos(angle)])
  half=(P['grip_length']-P['grip_width'])/2
  profile=LineString([-half*direction,half*direction]).buffer(P['grip_width']/2,quad_segs=16)
  ls=[];step=P['layer_step']
  for a in np.arange(-P['grip_depth'],0,step):
   ls.append((float(a),min(0.,float(a+step)),profile.buffer(float(a),quad_segs=16)))
  ls.append((0.,.8,profile))
  cut=prior.solid(ls)
  matrix=np.eye(4);matrix[:3,:3]=[[t[0],0,n[0]],[t[1],0,n[1]],[0,1,0]];matrix[:3,3]=[*(c+2.8*n),P['grip_z']]
  cut.apply_transform(matrix)
  GRIPS.append(dict(side=side,c=c,t=t,n=n,cutter=cut))

def cut_grips(mesh):
 cutters=[g['cutter'] for g in GRIPS if np.all(np.minimum(mesh.bounds[1],g['cutter'].bounds[1])-np.maximum(mesh.bounds[0],g['cutter'].bounds[0])>0)]
 return prior.old.stable(trimesh.boolean.difference([mesh,*cutters],engine='manifold')) if cutters else mesh
