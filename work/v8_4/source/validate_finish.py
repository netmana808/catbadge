"""Check exported finishing, preserved interfaces and mixing with v8.3 parts."""
import numpy as np
import trimesh
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import generate_v84 as g
from validate_v84 import req,iv,moved,quality,sec,close,load

def baseline(name):return trimesh.load_mesh(g.ROOT/'reference'/('v83_'+name+'_ASSEMBLY.stl'))
def check_finishing(lid,alt,rear,cover):
 oldlid=baseline('faceplate');oldalt=baseline('faceplate_NO_SPRING_ONLY');oldrear=baseline('rear_tray');oldcover=baseline('battery_cover');oldcap=baseline('cap_socket_3p2')
 changes={}
 for name,new,old in [('faceplate',lid,oldlid),('faceplate_NO_SPRING_ONLY',alt,oldalt),('rear_tray',rear,oldrear),('battery_cover',cover,oldcover),('cap_socket_3p2',load('cap_socket_3p2'),oldcap)]:
  added=trimesh.boolean.difference([new,old],engine='manifold')
  req(abs(added.volume)<.003,name+' added material outside original envelope')
  req(np.allclose(new.bounds,old.bounds,atol=.0001,rtol=0),name+' overall size changed')
  removed=old.volume-new.volume;req(removed>.1,name+' has no finishing')
  changes[name]={'removed_mm3':float(removed),'added_residual_mm3':abs(float(added.volume))}
 # Working cap body, stem, socket and flange must match the exported baseline.
 cap=load('cap_socket_3p2')
 for z in [5.301,5.6,6.799,7.,9.799,9.801,10.799,11.501,12.999]:close(sec(cap,z),sec(oldcap,z),'cap interface')
 face=sec(cap,13.299)
 req(abs(face.bounds[2]-4.701)<.0001 and abs(face.bounds[0]+4.701)<.0001,'button face bevel absent')
 # Exterior chamfers remove material only in the top/bottom 0.6 mm bands.
 for label,new,old,z,protected in [('front',lid,oldlid,12.799,g.PCB.buffer(.3)),('rear',rear,oldrear,-9.599,g.finish.REAR_PROTECT),('cover',cover,oldcover,-17.899,g.finish.COVER_PROTECT)]:
  delta=sec(old,z).difference(sec(new,z))
  req(delta.area>10,label+' exterior bevel absent')
  req(delta.intersection(protected).area<.001,label+' protected area trimmed')
 # Each of the eight grip cuts must exist, retain its floor and stay outside electronics.
 profile=sec(lid,7.2);previous=sec(oldlid,7.2);delta=previous.difference(profile)
 req(delta.intersection(g.PCB.buffer(.3)).area<.001,'grip enters electronics clearance')
 grips=[]
 for gr in g.finish.GRIPS:
  origin=gr['c']+2.8*gr['n'];region=Point(origin).buffer(1.4)
  cut=delta.intersection(region);req(.01<cut.area<1.,'missing or excessive grip cut')
  # At the center line, a floor remains 0.3 mm inward, with 0.2 mm visibly recessed.
  req(profile.contains(Point(origin-.3*gr['n'])),'grip floor missing')
  req(not profile.contains(Point(origin-.2*gr['n'])),'grip too shallow')
  grips.append(float(cut.area))
 # The release entrances widen only in their exterior mouths. Catches remain identical.
 delta=sec(oldlid,-.05).difference(sec(lid,-.05))
 for snap in g.SNAPS:
  region=g.slab(snap,3.8,7.2,2.4,4.)
  req(delta.intersection(region).area>.005,'release mouth bevel absent')
  for z in [-.8,-.3,.0,.5,1.79]:
   region=g.slab(snap,-3.,3.,0.,4.)
   close(sec(lid,z).intersection(region),sec(oldlid,z).intersection(region),'catch shape changed')
 # Cover wall top, tabs and actual flexible latch retain their old geometry.
 for z in [-17.899,-17.5,-12.,-9.8,-9.601,-9.599,-8.701,-7.,-6.801]:
  region=g.finish.COVER_PROTECT if z<-9.6 else box(-40,-60,40,40)
  close(sec(cover,z).intersection(region),sec(oldcover,z).intersection(region),'cover working interface')
 from validate_snaps import check_pair
 mixed={}
 for label,face,tray in [('new_lid_old_tray',lid,oldrear),('new_alt_old_tray',alt,oldrear),('old_lid_new_tray',oldlid,rear),('old_alt_new_tray',oldalt,rear)]:
  mixed[label]=check_pair(face,tray,range(4),g.P['release_deflection'])
 motions=[(float(x),0.) for x in np.linspace(0,3.2,17)]+[(3.2,float(z)) for z in np.linspace(-.25,-20,25)]
 for label,cov,tray in [('new_cover_old_tray',cover,oldrear),('old_cover_new_tray',oldcover,rear)]:
  req(iv(cov,tray)<.003,label+' rest collision')
  req(iv(moved(cov,(.6,0)),tray)>.02,label+' latch missing')
  req(iv(moved(cov,dz=-.6),tray)>1,label+' tabs missing')
  released=g.deflected_cover(cov,1.)
  for x,z in motions:req(iv(moved(released,(x,0),z),tray)<.005,label+' slide interference')
  mixed[label]={'release_positions':len(motions)}
 count=0
 for c,faces in [(oldcap,[lid,alt]),(cap,[oldlid,oldalt])]:
  for face in faces:
   for xy in g.v.BUTTONS.values():
    for dz in [0,.2,-.2,-.5,-.8]:req(iv(moved(c,xy,dz),face)<.002,'mixed cap binding');count+=1
    req(iv(moved(c,xy,1.1),face)>.1,'mixed cap stop missing')
 return {'material_removal':changes,'eight_grips_section_area_mm2':grips,'button_flat_face_diameter_mm':9.4,'mechanical_interface_sections_preserved':True,'mixed_v83_v84_assemblies':mixed,'mixed_button_motion_cases':count}
