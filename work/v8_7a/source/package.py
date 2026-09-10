"""Package only this local derivative; verify extracted files and meshes."""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import zipfile
import trimesh
from build import ROOT, quality


def main():
    assert json.loads((ROOT / 'validation.json').read_text())['status'] == 'PASS'
    dest = ROOT.parents[1] / 'dist/v8_7a'
    dest.mkdir(parents=True, exist_ok=True)
    for folder in ['parts', 'tests', 'source', 'reference', 'preview']:
        shutil.copytree(ROOT / folder, dest / folder, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ['README.md', 'validation.json', 'run.sh']:
        shutil.copy2(ROOT / name, dest / name)
    files = sorted(p for p in dest.rglob('*') if p.is_file()
                   and p.suffix != '.zip' and p.name not in ['SHA256SUMS', 'package-verification.json'])
    checksums = {str(p.relative_to(dest)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (dest / 'SHA256SUMS').write_text(''.join(f'{h}  {p}\n' for p, h in checksums.items()))
    archive = dest / 'CatBadge-v8.7a-Rear-Adhesion-Reprint.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in [*files, dest / 'SHA256SUMS']:
            z.write(p, p.relative_to(dest))
    with tempfile.TemporaryDirectory(prefix='catbadge-v87a-verify-') as temp:
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            z.extractall(temp)
        for relative, expected in checksums.items():
            p = Path(temp) / relative
            assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
            if p.suffix in ['.stl', '.3mf']:
                quality(trimesh.load(p, force='mesh'))
    report = dict(status='PASS', archive=archive.name, payload_files=len(files)+1,
                  sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                  extracted_checksums_and_meshes_verified=True)
    (dest / 'package-verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
