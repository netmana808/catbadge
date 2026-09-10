"""Export-based regression checks for closed floor and wider detents."""
import numpy as np
import trimesh
from shapely.geometry import Point,box
import generate_v87 as g
from validate_v87 import req,iv,moved,sec,close,load,quality

def ref(name):return trimesh.load_mesh(g.ROOT/'reference'/('v84_'+name+'_ASSEMBLY.stl'))
def check_revision(lid,alt,rear,cover):
 oldrear=ref('rear_tray');oldlid=ref('faceplate');oldcover=ref('battery_cover')
 req(abs(rear.bounds[0,2]+10.4)<.0001,'rear outside plane')
 for z in [-10.399,-9.801,-9.001,-8.001]:
  profile=sec(rear,z)
  for xy in [(-40,-3),(-40,-10),(-40,-17),(40,-3),(40,-10),(40,-17),(-45,26),(45,26)]:
   req(profile.contains(Point(xy).buffer(.5)),'rear window still open '+str(xy))
  for name,region in [('UART',g.HEADER_WINDOWS['UART']),('QWIIC',g.HEADER_WINDOWS['QWIIC']),('lanyard',g.v.LANYARD),('battery',g.v.D['battery'])]:
   req(profile.intersection(region.buffer(-.01)).area<.001,name+' rear access blocked')
 req(not sec(rear,-7.999).contains(Point(40,-10)),'rear electronics clearance reduced')
 gain=rear.volume-oldrear.volume;req(gain>2000,'rear closure missing')
 # Cover is unchanged geometry, translated outward for the thicker rear plate.
 shifted=moved(oldcover,dz=-.8)
 for a,b in [(cover,shifted),(shifted,cover)]:
  difference=trimesh.boolean.difference([a,b],engine='manifold');req(abs(difference.volume)<.003,'cover changed beyond datum shift')
 req(np.allclose(cover.bounds,shifted.bounds,atol=.0001,rtol=0),'cover shift')
 cap=load('cap_socket_3p2');oldcap=ref('cap_socket_3p2')
 req(np.allclose(cap.bounds,oldcap.bounds,atol=.0001,rtol=0) and abs(cap.volume-oldcap.volume)<.003,'button geometry changed')
 # Quantify the revised geometry; this does not measure retention force.
 ratios=[]
 for s in g.SNAPS:
  probe=g.solid([(-1.5,2.,g.slab(s,-4.3,4.3,-.1,4))])
  newlocal=trimesh.boolean.intersection([lid,probe],engine='manifold')
  oldlocal=trimesh.boolean.intersection([oldlid,probe],engine='manifold')
  new=iv(moved(newlocal,dz=.9),rear);old=iv(moved(oldlocal,dz=.9),oldrear)
  req(new>old*1.5,'revised catch engagement did not increase')
  ratios.append({'v84_lift_interference_mm3':old,'v87_lift_interference_mm3':new})
 # Thicker rim must remain outside the protected PCB envelope.
 for z in [-1.19,-.3,.5,1.79]:
  req(sec(lid,z).intersection(g.PCB.buffer(.3)).area<.001,'rim enters board envelope')
 # Preserve all existing side service paths above the floor.
 for z in [-7.999,-5.,-.001,.001,1.799]:
  for name,region in g.v.D['ports'].items():
   oldspace=region.difference(sec(oldrear,z))
   req(sec(rear,z).intersection(oldspace).area<.002,'service path narrowed '+name)
 return {'closed_former_vents_and_ear_windows':True,'rear_panel_thickness_mm':2.4,
         'rear_material_added_mm3':float(gain),'cover_translation_mm':[0,0,-.8],
         'v84_button_geometry_preserved':True,'catch_width_mm':8.,'tongue_nominal_thickness_mm':1.4,
         'catch_lift_interference_comparison':ratios,'required_rear_access_preserved':True,
         'physical_fit_force_and_fatigue':'UNVERIFIED; user reported poor earlier snap fit'}
