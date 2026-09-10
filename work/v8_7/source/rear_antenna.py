"""Trial metal-nut bulkhead port on the outer slope of the left ear, in rear tray."""
import math
import numpy as np
from shapely.geometry import Point,Polygon,MultiPoint
from shapely.ops import unary_union
import v03_reference as v
P=dict(target_xy=[-55.,28.],axis_z=-5.0,hole_diameter=6.5,roof_degrees=45.,
       land_width=11.,inner_plane=.4,outer_plane=2.8,floor_relief_z=-8.8,
       relief_depth=5.,taper_start=-3.,taper_end=-2.)
d=v.D['pcb'].exterior.project(Point(P['target_xy']))
C=np.array(v.D['pcb'].exterior.interpolate(d).coords[0]);T=np.array(v.D['pcb'].exterior.interpolate(d+.3).coords[0])-C;T/=np.linalg.norm(T)
N=np.array([T[1],-T[0]]);assert not v.D['pcb'].contains(Point(C+N))
def slab(t0,t1,n0,n1):return Polygon([C+t*T+n*N for t,n in [(t0,n0),(t1,n0),(t1,n1),(t0,n1)]])
PANEL=slab(-5.5,5.5,.4,2.8)
INNER_CUT=slab(-5.5,5.5,-5.,.4)
OUTER_CUT=slab(-5.5,5.5,2.8,8.)
REGION=slab(-8,8,-6,5.)
def revise(layers):
 def at(z):return next(p for a,b,p in layers if a-1e-7<=z<b+1e-7)
 zs=sorted(set(round(float(z),6) for z in [a for a,_,_ in layers]+[b for _,b,_ in layers]+[P['floor_relief_z']]+list(np.arange(-3.,-1.999,.1))))
 result=[]
 for a,b in zip(zs,zs[1:]):
  z=(a+b)/2;p=unary_union([at(z),PANEL]).difference(OUTER_CUT)
  if P['floor_relief_z']<=z<P['taper_start']:p=p.difference(INNER_CUT)
  elif P['taper_start']<=z<P['taper_end']:p=p.difference(INNER_CUT.buffer(-(z-P['taper_start'])*1.0))
  result.append((a,b,p))
 return result

def profile():
 radius=P['hole_diameter']/2
 return MultiPoint([(radius*math.cos(i*math.tau/128),radius*math.sin(i*math.tau/128)) for i in range(128)]+[(0,radius/math.cos(math.radians(P['roof_degrees'])))]).convex_hull

def cutter_scad(body):
 import json
 matrix=[[float(T[0]),0,float(N[0]),float(C[0])],[float(T[1]),0,float(N[1]),float(C[1])],[0,1,0,P['axis_z']],[0,0,0,1]]
 return 'difference(){\n'+body+'\nmultmatrix('+json.dumps(matrix)+') linear_extrude(height=20,center=true){'+v.scad_polygon(profile())+'}\n}\n'

def data():return {**P,'pcb_edge_xy':C.tolist(),'tangent_xy':T.tolist(),'outward_normal_xy':N.tolist(),'mount_outer_xy':(C+N*P['outer_plane']).tolist(),'source_adapter':{'reference':'J1','layer':'B.Cu','assembly_xy':[-42.53,34.]},'status':'TRIAL - actual connector dimensions and cable bend clearance not verified'}
