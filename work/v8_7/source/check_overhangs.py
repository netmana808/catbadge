"""Layer-to-layer support envelope in exported print orientation, at 0.2 mm."""
import json,sys
import numpy as np
import trimesh
from shapely.geometry import Polygon
from validate_v87 import sec,req
from generate_v87 import ROOT

def main():
 report={}
 for path in sorted(list((ROOT/'parts').glob('*.stl'))+list((ROOT/'tests').glob('*.stl'))):
  if '--coupons' in sys.argv and path.parent.name=='parts' and not path.name.startswith('cap_'):continue
  m=trimesh.load_mesh(path);height=m.bounds[1,2];below=sec(m,.0001);rows=[]
  for z in np.arange(.2001,height-.0001,.2):
   current=sec(m,float(z));unsupported=current.difference(below.buffer(.205,quad_segs=16))
   if unsupported.area>.025:rows.append({'z':float(z),'area_mm2':float(unsupported.area)})
   below=current
  report[path.stem]={'layer_height_mm':.2,'allowed_expansion_mm':.205,'violations':rows,'pass':not rows}
  print(path.stem,'PASS' if not rows else rows,flush=True)
 (ROOT/('overhangs_coupons.json' if '--coupons' in sys.argv else 'overhangs.json')).write_text(json.dumps(report,indent=2))
 req(all(r['pass'] for r in report.values()),'Unsupported expansion exceeds 45-degree envelope; see overhangs.json')
if __name__=='__main__':main()
