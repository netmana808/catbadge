"""Small standalone mesh/3MF helpers; all geometry dimensions are millimeters."""
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import manifold3d as mf
from shapely.geometry import Polygon

NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'


def solid(m):
    s = mf.Manifold(mf.Mesh64(np.asarray(m.vertices, dtype=np.float64),
                            np.asarray(m.faces, dtype=np.uint64)))
    assert s.status() == mf.Error.NoError
    return s


def quality(m, printable=True):
    assert np.isfinite(m.vertices).all() and m.is_watertight
    assert m.is_winding_consistent and m.volume > 0
    assert len(m.split(only_watertight=False)) == 1
    assert m.area_faces.min() > 1e-12
    if printable:
        assert m.bounds[0].min() > -1e-5
    return dict(volume_mm3=float(m.volume), bounds_mm=m.bounds.tolist(),
                triangles=len(m.faces), connected_solids=1, watertight=True)


def section(m, z):
    path = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    result = Polygon()
    if path:
        for loop in path.discrete:
            result = result.symmetric_difference(Polygon(loop[:, :2]))
    return result


def face_down(m):
    result = m.copy()
    result.vertices *= [1, -1, -1]  # Proper 180-degree rotation about X.
    result.apply_translation(-result.bounds[0])
    return result


def write_3mf(path, objects):
    model = ET.Element('model', xmlns=NS, unit='millimeter')
    resources = ET.SubElement(model, 'resources')
    build = ET.SubElement(model, 'build')
    for i, (name, m) in enumerate(objects.items(), 1):
        obj = ET.SubElement(resources, 'object', id=str(i), type='model', name=name)
        geom = ET.SubElement(obj, 'mesh')
        vertices = ET.SubElement(geom, 'vertices')
        for v in m.vertices:
            ET.SubElement(vertices, 'vertex', **dict(zip(('x', 'y', 'z'), map(str, v))))
        triangles = ET.SubElement(geom, 'triangles')
        for f in m.faces:
            ET.SubElement(triangles, 'triangle', **dict(zip(('v1', 'v2', 'v3'), map(str, f))))
        ET.SubElement(build, 'item', objectid=str(i))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('3D/3dmodel.model', ET.tostring(model, encoding='utf-8', xml_declaration=True))
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        doc = ET.fromstring(z.read('3D/3dmodel.model'))
        assert doc.get('unit') == 'millimeter'
        names = [o.get('name') for o in doc.findall(f'{{{NS}}}resources/{{{NS}}}object')]
        assert names == list(objects)
    scene = trimesh.load(path, force='scene')
    assert len(scene.graph.nodes_geometry) == len(objects)
    for node in scene.graph.nodes_geometry:
        matrix, key = scene.graph[node]
        m = scene.geometry[key].copy()
        m.apply_transform(matrix)
        quality(m)
        candidates = [ref for ref in objects.values() if np.allclose(ref.bounds, m.bounds, atol=1e-6, rtol=0)]
        assert len(candidates) == 1 and abs(candidates[0].volume - m.volume) < 1e-5


def export_pair(path, m):
    m.export(str(path) + '.stl')
    loaded = trimesh.load_mesh(str(path) + '.stl')
    report = quality(loaded)
    write_3mf(str(path) + '.3mf', {path.name: loaded})
    report['stl_3mf_agree'] = True
    return loaded, report
