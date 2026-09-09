"""Reload exports and check mechanical interfaces and motion independently."""
import json, math, hashlib, zipfile, warnings, sys
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import generate_v84 as g
ROOT=g.ROOT;NS={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
warnings.filterwarnings('ignore',category=RuntimeWarning,module='trimesh')
def req(ok,msg):
 if not ok:raise ValueError(msg)
def quality(m,name):
 req(np.isfinite(m.vertices).all() and m.is_watertight and m.is_winding_consistent and m.volume>0,name+' invalid mesh')
 req(len(m.split(only_watertight=False))==1,name+' disconnected')
 req(m.area_faces.min()>1e-12,name+' degenerate')
 return {'volume_mm3':float(m.volume),'bounds_mm':m.bounds.tolist(),'triangles':len(m.faces),'one_solid':True}
def iv(a,b):
 if np.any(np.minimum(a.bounds[1],b.bounds[1])-np.maximum(a.bounds[0],b.bounds[0])<1e-5):return 0.
 m=trimesh.boolean.intersection([a,b],engine='manifold')
 return abs(float(m.volume)) if len(m.faces) else 0.
def moved(m,xy=(0,0),dz=0):
 a=m.copy();a.apply_translation([*xy,dz]);return a
def sec(m,z):
 path=m.section(plane_origin=[0,0,z],plane_normal=[0,0,1]);out=Polygon()
 req(path is not None,f'missing section {z}')
 for loop in path.discrete:out=out.symmetric_difference(Polygon(loop[:,:2]))
 return out
def close(a,b,label):
 err=a.symmetric_difference(b).area
 req(err<.025,label+f' section mismatch {err}')
 return float(err)
def cylinder(radius,z0,z1,xy):
 m=trimesh.creation.cylinder(radius=radius,height=z1-z0,sections=128);m.apply_translation([*xy,(z0+z1)/2]);return m

def load(name):return trimesh.load_mesh(ROOT/'preview'/(name+'_ASSEMBLY.stl'))

def coupon_checks():
 from validate_snaps import coupon_checks as checks
 return checks()

def main():
 checks=coupon_checks()
 if '--coupons' in sys.argv:print('COUPON MECHANICS PASS',checks);return
 report={'status':'RUNNING','parts':{},'kits':{},'checks':checks}
 for path in sorted(list((ROOT/'parts').glob('*.stl'))+list((ROOT/'tests').glob('*.stl'))):
  m=trimesh.load_mesh(path);r=quality(m,path.stem);req(m.bounds[0].min()>-1e-5,'below print origin')
  mf=trimesh.load(path.with_suffix('.3mf'),force='mesh');quality(mf,path.stem+' 3MF')
  req(np.allclose(m.bounds,mf.bounds,atol=.0002,rtol=0) and abs(m.volume-mf.volume)<.03,'STL/3MF mismatch')
  for a,b in [(m,mf),(mf,m)]:
   pts,_=trimesh.sample.sample_surface(a,300,seed=7);_,dist,_=trimesh.proximity.closest_point(b,pts);req(dist.max()<.0002,'3MF surface mismatch')
  report['parts'][path.stem]=r
 for path in ROOT.glob('*.3mf'):
  with zipfile.ZipFile(path) as z:
   req(z.testzip() is None,'bad archive');doc=ET.fromstring(z.read('3D/3dmodel.model'))
  req(doc.get('unit')=='millimeter','units');req('v8.4' in doc.find("m:metadata[@name='Title']",NS).text,'title')
  objs=doc.findall('m:resources/m:object',NS);expected=(3 if 'Comfort_Only' in path.name else 15) if 'PRINT_FIRST' in path.name else 9;req(len(objs)==len(set(o.get('name') for o in objs))==expected,'kit count')
  scene=trimesh.load(path,force='scene');loaded=[]
  for name in scene.graph.nodes_geometry:
   matrix,key=scene.graph[name];m=scene.geometry[key].copy();m.apply_transform(matrix);quality(m,name)
   req(m.bounds[0].min()>-1e-5 and m.bounds[1,:2].max()<220,'kit bounds')
   refname='cap_socket_3p2' if name.startswith('button_') else name
   refpath=ROOT/'parts'/(refname+'.stl')
   if not refpath.exists():refpath=ROOT/'tests'/(refname+'.stl')
   ref=trimesh.load_mesh(refpath);req(np.allclose(m.extents,ref.extents,atol=.0002,rtol=0) and abs(m.volume-ref.volume)<.03,'kit part mismatch')
   for other in loaded:req(not np.all(np.minimum(m.bounds[1,:2],other.bounds[1,:2])-np.maximum(m.bounds[0,:2],other.bounds[0,:2])>0),'kit overlap')
   loaded.append(m)
  report['kits'][path.name]={'objects':expected,'bed_mm':[220,220],'no_overlap':True}
 lid=load('faceplate');alt=load('faceplate_NO_SPRING_ONLY');rear=load('rear_tray');cover=load('battery_cover');pcb=load('pcb_REFERENCE')
 assembled=[lid,rear,cover]
 for i,a in enumerate(assembled):
  for b in assembled[i+1:]:req(iv(a,b)<.003,'assembled collision '+str(i))
 for p in [lid,alt,rear]:req(iv(p,pcb)<.002,'PCB collision')
 for p in [rear,cover]:req(iv(alt,p)<.003,'alternate assembly collision')
 for z in [-.001,.001,1.799]:
  region=g.v.D['pcb'].buffer(.3)
  close(sec(rear,z).intersection(region),g.old.at(g.old.rear_layers(),z).intersection(region),'PCB seat changed')
 # Compare the electronics-facing lid area directly with the v8.3 exports.
 for name,face in [('faceplate',lid),('faceplate_NO_SPRING_ONLY',alt)]:
  baseline=trimesh.load_mesh(ROOT/'reference'/('v83_'+name+'_ASSEMBLY.stl'))
  for z in [1.801,4.201,9.001,9.801,11.201,12.001,12.799]:
   interior=g.PCB.buffer(.3)
   close(sec(face,z).intersection(interior),sec(baseline,z).intersection(interior),'v83 front interior')
 report['checks']['v83_front_interior_and_retaining_ribs_preserved']=True
 report['checks']['PCB_seat_and_assembly_clearance']=True
 from validate_snaps import check_pair
 report['checks']['full_integral_snaps']=check_pair(lid,rear,range(4),g.P['release_deflection'])
 report['checks']['alternate_integral_snaps']=check_pair(alt,rear,range(4),g.P['release_deflection'])
 # Release access lies outside the PCB, beside each integral catch.
 for i,snap in enumerate(g.SNAPS):
  access=g.solid([(-1.15,-.15,g.slab(snap,4.2,6.8,1.7,4.5))])
  for part in [lid,alt,rear,pcb]:req(iv(access,part)<.002,'release notch obstructed '+str(i))
 report['checks']['four_external_release_notches']=True
 n=0
 for dia in g.old.P['socket_trials']:
  cap=load(f'cap_socket_{dia:.1f}'.replace('.','p'))
  for xy in g.v.BUTTONS.values():
   for dz in [0,.2,-.2,-.5,-.8]:
    for face in [lid,alt]:req(iv(moved(cap,xy,dz),face)<.002,'button binding')
    n+=1
   req(iv(moved(cap,xy,1.1),lid)>.1,'outward flange stop absent')
 report['checks']['button_motion_cases_both_lids']=n
 holder=trimesh.creation.box(extents=[32.7,59.7,15.7]);holder.apply_translation([0,-10,-7.85])
 for p in [rear,cover]:req(iv(p,holder)<.002,'battery holder collision')
 req(iv(moved(cover,(.6,0)),rear)>.02,'battery cover not latched')
 req(iv(moved(cover,dz=-.6),rear)>1,'battery cover tabs no longer retain')
 released=g.deflected_cover(cover,1.)
 for d in np.linspace(0,1,6):
  m=g.deflected_cover(cover,float(d))
  for p in [rear,holder]:req(iv(m,p)<.005,'latch deflection collision')
 motions=[(float(x),0.) for x in np.linspace(0,3.2,17)]+[(3.2,float(z)) for z in np.linspace(-.25,-20,25)]
 for x,z in motions:
  m=moved(released,(x,0),z)
  for p in [rear,holder]:req(iv(m,p)<.005,f'battery cover release collision {x} {z}')
 report['checks']['cover_release_positions']=len(motions)
 # Screen, all ten LED footprints and the rotated SAO access remain open.
 sao=g.old.ears.SAO_COURTYARD
 for face in [lid,alt]:
  for z in [11.201,12.,12.799]:
   profile=sec(face,z);req(profile.intersection(g.v.screen_hole()).area<.001,'screen blocked')
   for x,y in g.old.ears.LEDS.values():req(profile.intersection(box(x-1,y-1,x+1,y+1)).area<.0001,'LED covered')
   req(profile.intersection(sao.buffer(1.49)).area<.0001,'SAO blocked')
  req(iv(face,g.solid([(1.8,13.,sao)]))<.002,'SAO plug path blocked')
 req(iv(lid,g.solid([(11.2,13.,g.old.ears.SPRING_OPEN)]))<.002,'spring access blocked')
 report['checks']['screen_LED_SAO_spring_access']=True
 # Independently measure the exported aperture.
 expected_bounds=np.array([-26.04,-27.99,26.46,12.01])
 from shapely.geometry import LineString
 for name,face in [('faceplate',lid),('faceplate_NO_SPRING_ONLY',alt)]:
  for z in [11.201,12.,12.799]:
   profile=sec(face,z)
   windows=[Polygon(ring) for poly in g.old.polygons(profile) for ring in poly.interiors if Polygon(ring).contains(Point(0,-7.99))]
   req(len(windows)==1,'screen aperture not a single opening')
   req(np.allclose(windows[0].bounds,expected_bounds,atol=.00005,rtol=0),'screen edges differ from requested coordinates')
 report['checks']['screen_opening_mm']={'size':[52.5,40.],'bounds_xy':expected_bounds.tolist()}

 ant=g.old.antenna;probe=trimesh.creation.cylinder(radius=3.2,height=8,sections=128)
 matrix=np.eye(4);matrix[:3,:3]=[[ant.T[0],0,ant.N[0]],[ant.T[1],0,ant.N[1]],[0,1,0]];matrix[:3,3]=[*ant.C,ant.P['axis_z']];probe.apply_transform(matrix)
 req(iv(probe,rear)<.002,'antenna port blocked')
 panel=sec(rear,-5.)
 for t in [-4.5,4.5]:
  for n in [.5,2.7]:req(panel.contains(Point(ant.C+t*ant.T+n*ant.N)),'antenna bearing land absent')
 for n in [.25,2.95]:req(not panel.contains(Point(ant.C+4.5*ant.T+n*ant.N)),'antenna panel thickness differs')
 report['checks']['rear_antenna_trial_clearance_and_2p4_land']=True
 for z in [-8.001,-.001,.001,1.799]:
  region=g.v.D['pcb'].buffer(.3).difference(g.old.antenna.REGION)
  close(sec(rear,z).intersection(region),g.old.at(g.old.rear_layers(),z).intersection(region),'rear internal envelope')
 if '--standalone' not in sys.argv:
  for name,sha in json.loads((ROOT/'input_hashes.json').read_text()).items():req(hashlib.sha256((ROOT.parents[1]/name).read_bytes()).hexdigest()==sha,'protected input changed')
  report['checks']['protected_inputs']=True
 from validate_finish import check_finishing
 report['checks']['v84_finishing_and_v83_compatibility']=check_finishing(lid,alt,rear,cover)

 paths=list((ROOT/'source').glob('*.py'))+list((ROOT/'parts').glob('*'))+list((ROOT/'tests').glob('*'))+list((ROOT/'reference').glob('*'))+list((ROOT/'preview').glob('*_ASSEMBLY.stl'))+list(ROOT.glob('*.3mf'))+[ROOT/'parameters.json',ROOT/'layouts.json',ROOT/'README.md',ROOT/'run.sh',ROOT/'requirements-resolved.txt']
 report['validated_artifacts']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
 report['dimensions_mm']={'main_shell':round(lid.bounds[1,2]-rear.bounds[0,2],3),'battery_shell':round(lid.bounds[1,2]-cover.bounds[0,2],3),'including_button_faces':round(load('cap_socket_3p2').bounds[1,2]-cover.bounds[0,2],3),'shell_width':float(lid.extents[0])}
 report['status']='PASS';(ROOT/'validation.json').write_text(json.dumps(report,indent=2));print('PASS',len(report['parts']),'parts',report['checks'])
if __name__=='__main__':main()
