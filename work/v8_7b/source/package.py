"""Local archive creation and extracted-payload verification; no publication."""
from pathlib import Path
import hashlib
import json
import tempfile
import zipfile
import shutil
import trimesh
from build import ROOT
from mesh_io import quality


def main():
    assert json.loads((ROOT/'validation.json').read_text())['status'] == 'PASS'
    dest = ROOT.parents[1]/'dist/v8_7b'
    dest.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in ROOT.rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts and p.suffix != '.pyc')
    checksums = {}
    for p in files:
        relative = p.relative_to(ROOT)
        output = dest/relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, output)
        checksums[str(relative)] = hashlib.sha256(output.read_bytes()).hexdigest()
    (dest/'SHA256SUMS').write_text(''.join(f'{digest}  {path}\n' for path,digest in checksums.items()))
    archive = dest/'CatBadge-v8.7b-Taller-Buttons.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in [*checksums, 'SHA256SUMS']:
            z.write(dest/name,name)
    mesh_count = 0
    with tempfile.TemporaryDirectory(prefix='catbadge-v87b-verify-') as temp:
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            z.extractall(temp)
        for relative, expected in checksums.items():
            p = Path(temp)/relative
            assert hashlib.sha256(p.read_bytes()).hexdigest() == expected
            if p.suffix == '.stl':
                quality(trimesh.load_mesh(p), printable='ASSEMBLY' not in p.name)
                mesh_count += 1
            elif p.suffix == '.3mf':
                scene = trimesh.load(p,force='scene')
                expected_count = 1 if 'parts/' in relative else 6
                assert len(scene.graph.nodes_geometry) == expected_count
                for node in scene.graph.nodes_geometry:
                    matrix,key = scene.graph[node]
                    m = scene.geometry[key].copy(); m.apply_transform(matrix)
                    quality(m); mesh_count += 1
    report = dict(status='PASS', archive=archive.name, payload_files=len(checksums)+1,
                  archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                  extracted_checksums_verified=True, extracted_solids_checked=mesh_count)
    (dest/'package-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
