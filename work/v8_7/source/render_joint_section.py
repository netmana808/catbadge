"""Draw a measured cross-section of the exported mating meshes."""
from PIL import Image,ImageDraw
import numpy as np
import trimesh
from shapely.geometry import Polygon
import generate_v87 as g
import render_v6 as r

def main():
 im=Image.new('RGB',(1600,1120),'#0C121B');d=ImageDraw.Draw(im)
 d.text((40,25),'V8.7 / INTEGRAL SNAP CROSS-SECTION',font=r.font(34,True),fill='#EAF2F5')
 d.text((40,80),'Section of exported meshes through the upper-left catch; PCB is a simplified reference.',font=r.font(20),fill='#AAC2CD')
 s=g.SNAPS[0];scale=168.;origin=(330,515)
 def xy(p):return (origin[0]+p[0]*scale,origin[1]-p[1]*scale)
 def poly(p,col):
  if p.geom_type=='MultiPolygon':
   for q in p.geoms:poly(q,col)
  elif p.geom_type=='Polygon':
   d.polygon([xy(q) for q in p.exterior.coords],fill=col)
   for hole in p.interiors:d.polygon([xy(q) for q in hole.coords],fill='#0C121B')
 for name,col in [('rear_tray','#527882'),('faceplate','#A4D8E8')]:
  m=trimesh.load_mesh(g.ROOT/'preview'/(name+'_ASSEMBLY.stl'))
  section=m.section(plane_origin=[*s['c'],0],plane_normal=[*s['t'],0]);shape=Polygon()
  for loop in section.discrete:
   points=np.column_stack(((loop[:,:2]-s['c'])@s['n'],loop[:,2]));p=Polygon(points)
   if p.is_valid:shape=shape.symmetric_difference(p)
  from shapely.geometry import box
  poly(shape.intersection(box(-1.6,-2.3,4,2.1)),col)
 poly(Polygon([(-1.5,0),(0,0),(0,1.6),(-1.5,1.6)]),'#205B45')
 for z in [-2,-1,0,1,2]:
  y=xy((0,z))[1];d.line((48,y,65,y),fill='#91A6AF',width=2);d.text((30,y),str(z),font=r.font(18),fill='#91A6AF',anchor='rm')
 d.text((45,975),'Z relative to PCB underside (mm)',font=r.font(19),fill='#91A6AF')
 d.text((370,975),'Outward from board edge  →',font=r.font(19),fill='#91A6AF')
 items=[('FACEPLATE','#A4D8E8'),('REAR TRAY','#527882'),('PCB REFERENCE','#205B45')]
 for i,(title,color) in enumerate(items):
  y=170+i*55;d.rectangle((995,y,1015,y+20),fill=color);d.text((1030,y-3),title,font=r.font(21,True),fill='#EAF2F5')
 for i,line in enumerate(['Overlapping rim aligns the halves.','Four wider catches retain them.','0.30 mm nominal rim gap.','0.35 mm selected trial engagement.','Release notches sit beside catches.','Flex rim outward to disengage.']):
  d.text((995,410+i*46),line,font=r.font(20),fill='#EAF2F5')
 # Point at the integral detent without obscuring its section.
 target=xy((.75,-.3));d.line([(960,775),(910,775),target],fill='#FFB579',width=3);d.ellipse((target[0]-5,target[1]-5,target[0]+5,target[1]+5),fill='#FFB579')
 d.text((995,753),'Built-in catch',font=r.font(22,True),fill='#FFB579')
 d.text((40,1050),'Actual CAD section / Ramps follow the 45° print envelope / Physical fit and retention force untested',font=r.font(22),fill='#FFD0A8')
 im.save(g.ROOT/'preview/snap_detail.png')
if __name__=='__main__':main()
