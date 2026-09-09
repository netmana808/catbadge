"""Independent exported-joint interference checks; no structural simulation."""
import numpy as np
import trimesh
from shapely.geometry import Point,box
import generate_v84 as g
from validate_v84 import req,iv,moved,quality,sec

def load(name):return trimesh.load_mesh(g.ROOT/'preview'/(name+'_ASSEMBLY.stl'))
def check_pair(lid,rear,indices,delta):
 req(iv(lid,rear)<.003,'rim rest collision')
 retained=[]
 for i in indices:
  region=g.slab(g.SNAPS[i],-3,3,-.1,4)
  probe=g.solid([(-1.5,2.,region)])
  local=trimesh.boolean.intersection([lid,probe],engine='manifold')
  overlap=iv(moved(local,dz=.9),rear)
  req(overlap>.025,f'catch {i} has no retention: {overlap}')
  retained.append(float(overlap))
 # Check deflection into a clear exterior followed by axial separation.
 for d in np.linspace(0,delta,6):
  release=g.released_lid(lid,float(d),indices)
  quality(release,'prescribed deflected lid')
  req(iv(release,rear)<.005,'rim outward release blocked')
 released=g.released_lid(lid,delta,indices)
 for z in np.concatenate([np.arange(0,3.21,.2),[4,6,10,15,25]]):
  req(iv(moved(released,dz=float(z)),rear)<.005,f'rim lift blocked at {z}')
 return {'retention_interference_mm3':retained,'release_positions':22,'prescribed_outward_mm':delta}

def coupon_checks():
 rows={};rear=load('PRINT_FIRST_rim_tray')
 for overlap in g.P['catch_trials']:
  label=str(round(overlap,2)).replace('.','p');lid=load('PRINT_FIRST_rim_lid_'+label)
  rows[label]=check_pair(lid,rear,[0],overlap+.2)
 lid=load('PRINT_FIRST_latch_cover');rear=load('PRINT_FIRST_latch_tray')
 req(iv(lid,rear)<.002,'cover latch rest collision')
 req(iv(moved(lid,(.6,0)),rear)>.02,'battery latch does not lock slide')
 released=g.deflected_cover(lid,1.)
 for x in np.linspace(0,3.2,17):req(iv(moved(released,(float(x),0)),rear)<.005,f'latch slide blocked {x}')
 return {'integral_snap_coupons':rows,'latch_coupon_release_positions':17}
if __name__=='__main__':print(coupon_checks())
