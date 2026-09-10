"""v8.7a: union sacrificial bed pads with the unchanged v8.7 rear tray.

Run using catbadge/.venv/bin/python. All dimensions are millimeters.
The included reference STL is the geometry source; no legacy generator imports.
"""
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
import manifold3d as mf
from shapely.geometry import Polygon, Point
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PAD_HEIGHT = 0.4
PADS = [(26.266, 98, 12), (121.70, 98, 12), (7, 8, 10), (141, 8, 10)]


def solid(mesh):
    result = mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                 np.asarray(mesh.faces, dtype=np.uint64)))
    assert result.status() == mf.Error.NoError
    return result


def mesh(s):
    m = s.to_mesh64()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=True)


def section(m, z):
    p = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    out = Polygon()
    if p is not None:
        for loop in p.discrete:
            out = out.symmetric_difference(Polygon(loop[:, :2]))
    return out


def quality(m):
    assert np.isfinite(m.vertices).all()
    assert m.is_watertight and m.is_winding_consistent and m.volume > 0
    assert len(m.split(only_watertight=False)) == 1
    assert m.area_faces.min() > 1e-12
    assert m.bounds[0].min() > -1e-5
    return dict(volume_mm3=float(m.volume), bounds_mm=m.bounds.tolist(),
                triangles=len(m.faces), connected_solids=1, watertight=True)


def export(m, folder, name):
    path = ROOT / folder / name
    # Collapse boolean slivers below STL float32 precision before serialization.
    m = mesh(solid(m).simplify(0.00001))
    m.export(path.with_name(path.name + '.stl'))
    m = trimesh.load_mesh(path.with_name(path.name + '.stl'))
    # Use the reloaded STL vertices for exact agreement between delivery formats.
    ns = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
    model = ET.Element('model', xmlns=ns, unit='millimeter')
    resources = ET.SubElement(model, 'resources')
    obj = ET.SubElement(resources, 'object', id='1', type='model', name=name)
    geom = ET.SubElement(obj, 'mesh')
    vertices = ET.SubElement(geom, 'vertices')
    for v in m.vertices:
        ET.SubElement(vertices, 'vertex', **dict(zip(('x', 'y', 'z'), map(str, v))))
    triangles = ET.SubElement(geom, 'triangles')
    for f in m.faces:
        ET.SubElement(triangles, 'triangle', **dict(zip(('v1', 'v2', 'v3'), map(str, f))))
    ET.SubElement(ET.SubElement(model, 'build'), 'item', objectid='1')
    with zipfile.ZipFile(path.with_name(path.name + '.3mf'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('3D/3dmodel.model', ET.tostring(model, encoding='utf-8', xml_declaration=True))
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    report = quality(m)
    other = trimesh.load(path.with_name(path.name + '.3mf'), force='mesh')
    quality(other)
    assert np.allclose(m.bounds, other.bounds, atol=1e-6, rtol=0)
    assert abs(m.volume - other.volume) < 1e-5
    with zipfile.ZipFile(path.with_name(path.name + '.3mf')) as z:
        doc = ET.fromstring(z.read('3D/3dmodel.model'))
        assert doc.get('unit') == 'millimeter'
        assert len(doc.findall(f'{{{ns}}}resources/{{{ns}}}object')) == 1
        assert doc.find(f'{{{ns}}}resources/{{{ns}}}object').get('name') == name
    report['stl_3mf_agree'] = True
    return m, report


def main():
    ref = ROOT / 'reference/rear_tray_v87.stl'
    original = trimesh.load_mesh(ref)
    base = solid(original)
    footprint = section(original, 0.1)
    pads = []
    for x, y, r in PADS:
        cylinder = trimesh.creation.cylinder(radius=r, height=PAD_HEIGHT, sections=128)
        cylinder.apply_translation([x, y, PAD_HEIGHT / 2])
        assert footprint.intersection(Point(x, y).buffer(r)).area > 10
        pads.append(solid(cylinder))
    padded = mf.Manifold.batch_boolean([base, *pads], mf.OpType.Add)
    # Crop a real ear tip with its actual pad as a small removal/first-layer coupon.
    clip = trimesh.creation.box(extents=[34, 28, 2.4])
    clip.apply_translation([26.266, 96, 1.2])
    coupon = mesh(padded ^ solid(clip))
    coupon.apply_translation(-coupon.bounds[0])
    coupon, coupon_report = export(coupon, 'tests', 'PRINT_FIRST_v8.7a_Ear_Pad_Removal')
    result = mesh(padded)
    shift = np.array([-result.bounds[0, 0], -result.bounds[0, 1], 0])
    result.apply_translation(shift)
    result, part_report = export(result, 'parts', 'CatBadge-v8.7a-Rear-Tray-Adhesion-Tabs')
    comparison = result.copy()
    comparison.apply_translation(-shift)
    actual = solid(comparison)
    missing = abs((base - actual).volume())
    added = actual - base
    assert missing < 0.003, ('original case removed', missing)
    above = trimesh.creation.box(extents=[400, 400, 40])
    above.apply_translation([70, 50, PAD_HEIGHT + .0001 + 20])
    added_above_pads = abs((added ^ solid(above)).volume())
    assert added_above_pads < .003, ('non-pad addition', added_above_pads)
    assert mesh(added).bounds[0, 2] > -0.0001
    # All battery/antenna holes remain open: additions stay outside the exterior outline.
    shell = Polygon(footprint.exterior)
    assert section(comparison, .1).difference(footprint).intersection(shell).area < .003
    section_errors = []
    unsupported = []
    below = section(comparison, .0001)
    for z in np.arange(.2001, original.bounds[1, 2], .2):
        current = section(comparison, z)
        if z > PAD_HEIGHT:
            error = current.symmetric_difference(section(original, z)).area
            section_errors.append(float(error))
            assert error < .025, ('interface changed', z, error)
        area = current.difference(below.buffer(.205, quad_segs=16)).area
        if area > .025:
            unsupported.append([float(z), float(area)])
        below = current
    assert not unsupported, unsupported
    assert np.all(result.extents[:2] + 16 < 220), '8 mm brim does not fit M5C'
    report = dict(status='PASS', reference_sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),
                  pad_height_mm=PAD_HEIGHT, pad_centers_radii_reference_xy=PADS,
                  print_translation_mm=shift.tolist(), rear=part_report, coupon=coupon_report,
                  original_removed_volume_mm3=missing, added_above_pads_mm3=added_above_pads, added_volume_mm3=abs(added.volume()),
                  added_bed_contact_mm2=float(section(comparison,.1).area-footprint.area),
                  max_section_error_above_pads_mm2=max(section_errors),
                  layer_check=dict(layer_mm=.2, lateral_allowance_mm=.205, unsupported=unsupported),
                  physical_print_test='PENDING', slicer_toolpath_validation='NOT PERFORMED')
    (ROOT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    # Measured horizontal sections from delivered STL, not an illustrative concept.
    im = Image.new('RGB', (1200, 960), '#12212c')
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 24) if Path('/System/Library/Fonts/Supplemental/Arial.ttf').exists() else ImageFont.load_default(size=24)
    def draw_shape(shape, color):
        for p in getattr(shape, 'geoms', [shape]):
            points = lambda ring: [(90 + x*6, 805-y*6) for x,y in ring.coords]
            d.polygon(points(p.exterior), fill=color)
            for hole in p.interiors:
                d.polygon(points(hole), fill='#12212c')
    draw_shape(section(comparison,.1), '#ffb45d')
    draw_shape(footprint, '#81bdcd')
    d.text((45,25), 'CatBadge v8.7a | rear tray only | removable bed pads',font=font,fill='white')
    d.text((45,65), 'Actual STL section at Z = 0.10 mm; view from above the print bed',font=font,fill='white')
    d.text((45,860), 'Orange: trim after cooling. Blue: unchanged v8.7 case footprint.',font=font,fill='white')
    d.text((45,903), 'Pads: 0.4 mm thick / 24 mm at ears / 20 mm at lower corners. UNPRINTED.',font=font,fill='white')
    im.save(ROOT / 'preview/bed-contact.png')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
