"""Taller button replacements for the unchanged v8.7 faceplate.

Profile derived from v8.7/source/finish_v84.py and generate_v75.py.
Board underside is assembly Z=0. No switch travel/force is inferred from CAD.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import trimesh
from mesh_io import export_pair, face_down, quality, section, solid, write_3mf

ROOT = Path(__file__).resolve().parents[1]
BUTTONS = {'LEFT': (-62., 0.), 'UP': (-53., 8.), 'DOWN': (-53., -8.),
           'RIGHT': (-44., 0.), 'B': (54.8, -9.7), 'A': (61., 3.)}
VARIANTS = [(10., 3.2), (10.2, 3.2), (10.3, 3.2), (10.2, 3.3), (10.2, 3.1), (10.2, 3.)]
P = dict(faceplate_outer_z=12.8, face_z=14.3, old_face_z=13.3, bevel=.3,
         socket_roof_z=6.8, socket_depth=1.5, socket_boss_diameter=4.8,
         flange_diameter=11.4, flange_bottom=9.8, flange_top=10.8,
         faceplate_guide_diameter=10.6, flange_cavity_diameter=11.8,
         status='UNPRINTED fit trial; same v8.7 faceplate')


def name(guide, socket):
    return f'cap_G{guide:.1f}_S{socket:.1f}_PLUS1mm'.replace('.', 'p')


def cap_mesh(guide, socket):
    mouth = P['socket_roof_z'] - P['socket_depth']
    flange_r, face_r = P['flange_diameter']/2, guide/2
    # Keep a true 45-degree flare in the face-down build direction.
    chamfer_top = P['flange_top'] + flange_r - face_r
    tip, top, bevel = P['socket_roof_z'], P['face_z'], P['bevel']
    boss = P['socket_boss_diameter']/2
    profile = [(0, tip), (socket/2, tip), (socket/2, mouth+.2),
               (socket/2+.15, mouth), (boss, mouth), (boss, P['flange_bottom']),
               (flange_r, P['flange_bottom']), (flange_r, P['flange_top']), (face_r, chamfer_top),
               (face_r, top-bevel), (face_r-bevel, top), (0, top), (0, tip)]
    return trimesh.creation.revolve(profile, sections=128)


def placed(m, xyz):
    result = m.copy()
    result.apply_translation(xyz)
    return result


def layout(meshes):
    objects = {}
    for i, (key, m) in enumerate(meshes.items()):
        objects[key] = placed(m, [8+24*(i%3), 8+24*(i//3), 0])
    for i, m in enumerate(objects.values()):
        assert np.all(m.bounds[1, :2] + 8 < 220)
        for other in list(objects.values())[:i]:
            # At least 4 mm separating XY boxes; layout is geometry only.
            assert np.any(np.maximum(m.bounds[0,:2], other.bounds[0,:2]) -
                          np.minimum(m.bounds[1,:2], other.bounds[1,:2]) > 4)
    return objects


def main():
    for directory in ['parts', 'tests', 'preview']:
        (ROOT / directory).mkdir(exist_ok=True)
    prints, assemblies, reports = {}, {}, {}
    for guide, socket in VARIANTS:
        key = name(guide, socket)
        assembly = cap_mesh(guide, socket)
        printable, report = export_pair(ROOT/'parts'/key, face_down(assembly))
        # Transform the actual STL back into its board-relative assembly position.
        actual = printable.copy()
        actual.apply_translation([-5.7, -5.7, -P['face_z']])
        actual.vertices *= [1, -1, -1]
        quality(actual, printable=False)
        actual.export(ROOT/'preview'/(key+'_ASSEMBLY.stl'))
        ref = trimesh.load_mesh(ROOT/'reference'/('cap_socket_'+f'{socket:.1f}'.replace('.', 'p')+'_ASSEMBLY.stl'))
        # Switch contact, socket entry/boss, flange and lower shoulder are unchanged.
        errors = []
        for z in [5.301, 5.4, 5.7, 6.799, 6.801, 8., 9.799, 9.801, 10.799]:
            err = section(actual, z).symmetric_difference(section(ref, z)).area
            assert err < .0002, ('switch interface changed', key, z, err)
            errors.append(float(err))
        assert abs(actual.bounds[1,2] - ref.bounds[1,2] - 1) < .00001
        assert abs(section(actual, 12.4).bounds[2] - guide/2) < .00001
        below = section(printable, .0001)
        overhangs = []
        for z in np.arange(.2001, printable.bounds[1,2]-.0001, .2):
            current = section(printable, z)
            area = current.difference(below.buffer(.205, quad_segs=16)).area
            if area > .025:
                overhangs.append([float(z), float(area)])
            below = current
        assert not overhangs, (key, overhangs)
        reports[key] = dict(**report, guide_diameter_mm=guide, socket_diameter_mm=socket,
                           guide_radial_clearance_mm=(10.6-guide)/2,
                           max_preserved_interface_section_error_mm2=max(errors),
                           nominal_protrusion_mm=P['face_z']-P['faceplate_outer_z'], layer_overhang_failures=overhangs)
        prints[key], assemblies[key] = printable, actual
    # Six small fit trials are created before the full replacement sets.
    write_3mf(ROOT/'PRINT_FIRST_v8.7b_Button_Fit_Trials.3mf', layout(prints))
    (ROOT/'parameters.json').write_text(json.dumps(dict(**P, variants=VARIANTS, button_positions=BUTTONS), indent=2)+'\n')
    count, stop_count, max_collision = 0, 0, 0.
    for face_name in ['faceplate_ASSEMBLY', 'faceplate_NO_SPRING_ONLY_ASSEMBLY']:
        face = solid(trimesh.load_mesh(ROOT/'reference'/(face_name+'.stl')))
        for button, (x,y) in BUTTONS.items():
            # Region contains each cap through every tested motion; cropping only accelerates booleans.
            region = trimesh.creation.box(extents=[16,16,24])
            region.apply_translation([x,y,10])
            local_face = face ^ solid(region)
            for key, m in assemblies.items():
                poses = [(0,0,z) for z in [-.8,-.5,-.2,0,.2]] + [(dx,dy,0) for dx,dy in [(.1,0),(-.1,0),(0,.1),(0,-.1)]]
                for dx,dy,dz in poses:
                    cap = solid(placed(m,[x+dx,y+dy,dz]))
                    volume = abs((cap ^ local_face).volume())
                    max_collision = max(max_collision, volume)
                    assert volume < .002, ('button collision',face_name,button,key,dx,dy,dz,volume)
                    count += 1
                stop_volume = abs((solid(placed(m,[x,y,1.1])) ^ local_face).volume())
                assert stop_volume > .1, ('flange stop missing', key, button)
                stop_count += 1
    # Adjacent directional buttons are close; verify their flanges do not overlap.
    for key, m in assemblies.items():
        group = [solid(placed(m,[x,y,0])) for x,y in BUTTONS.values()]
        for i,a in enumerate(group):
            for b in group[:i]:
                assert abs((a ^ b).volume()) < .002
    for key, m in prints.items():
        write_3mf(ROOT/f'CatBadge-v8.7b-SIX-{key}.3mf',
                  layout({f'{button}_{key}': m for button in BUTTONS}))
    report = dict(status='PASS', parts=reports, collision_free_motion_cases=count,
                  flange_stop_cases=stop_count, max_collision_volume_mm3=max_collision,
                  actual_switch_stroke_force_and_return='UNVERIFIED', physical_fit='UNPRINTED',
                  slicer_toolpaths='NOT VALIDATED', front_and_rear_modified=False,
                  reference_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'reference').glob('*.stl'))})
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['parts','reference_sha256']},indent=2))


if __name__ == '__main__':
    main()
