"""Package only the validated V8.7 prototype; no printer operations."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parent.parent;PROJECT=ROOT.parents[1];OUT=PROJECT/'dist/v8_7'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 report=json.loads((ROOT/'validation.json').read_text());assert report['status']=='PASS'
 overhang=json.loads((ROOT/'overhangs.json').read_text());assert set(overhang)==set(report['parts']) and all(v['pass'] for v in overhang.values())
 for name,value in report['validated_artifacts'].items():assert sha(ROOT/name)==value,'Stale validation: '+name
 for name,value in json.loads((ROOT/'input_hashes.json').read_text()).items():assert sha(PROJECT/name)==value,'Protected input changed: '+name
 OUT.mkdir(parents=True,exist_ok=True)
 for p in list(ROOT.glob('*.3mf'))+[ROOT/n for n in ['README.md','validation.json','overhangs.json']]:shutil.copy2(p,OUT/p.name)
 for name in ['faceplate','faceplate_NO_SPRING_ONLY','rear_tray','battery_cover']:
  shutil.copy2(ROOT/'parts'/(name+'.3mf'),OUT/('CatBadge-v8.7-'+name+'.3mf'))
 shutil.copy2(ROOT/'tests/PRINT_FIRST_screen_52p5x40.3mf',OUT/'PRINT_FIRST_screen_52p5x40.3mf')
 for name in ['front','closed_ears','rear','snap_detail','rim_inside','latch','antenna','comfort']:shutil.copy2(ROOT/'preview'/(name+'.png'),OUT/(name+'.png'))
 files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('debug') and not p.name.endswith('_raw.png')]
 archive=OUT/'CatBadge-v8.7-Closed-Back-Case.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(files):z.write(p,'CatBadge-v8.7/'+str(p.relative_to(ROOT)))
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for p in files:assert hashlib.sha256(z.read('CatBadge-v8.7/'+str(p.relative_to(ROOT)))).hexdigest()==sha(p)
 checks={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name not in ['SHA256SUMS','package_report.json']}
 (OUT/'SHA256SUMS').write_text(''.join(f'{v}  {n}\n' for n,v in sorted(checks.items())))
 (OUT/'package_report.json').write_text(json.dumps({'archive_members':len(files),'CRC_and_content_hashes':'PASS','validated_before_packaging':True,'checksums':checks},indent=2))
 print('Packaged',archive,'with',len(files),'files')
if __name__=='__main__':main()
