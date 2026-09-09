#!/usr/bin/env python3
"""CatBadge measured-height faceplate v0.3. Python 3.10+.

Reuses the v0.1 mounting/PCB retaining interface, then builds a taller lid.
Datum: underside of the green main PCB = assembly Z=0. Units: millimetres.
No complete component STEP assembly was available. See README for limitations.
"""
from __future__ import annotations
import json, math, hashlib, zipfile, time
from pathlib import Path
from typing import Any
import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, LineString, box, mapping
from shapely.ops import unary_union
from shapely import affinity
from build_case import make_design, PARAMS as ORIGINAL_PARAMS, circle, round_box, native_box, scad_polygon
from mesh_tools import layered_mesh, export_3mf

ROOT=Path(__file__).resolve().parent.parent
for sub in ('parts','tests','preview','reference'): (ROOT/sub).mkdir(exist_ok=True)
P={
 'pcb_underside_to_screen_top':10.5,
 'pcb_underside_to_unpressed_button_top':6.8,
 'pcb_underside_to_switch_housing_BOTTOM':3.99,
 'screen_clearance':0.7,
 'roof_thickness':2.0,
 'screen_aperture_width':52.5,
 'screen_aperture_height':40.0,
 'screen_chamfer_width':1.0,
 'screen_chamfer_height':1.0,
 'chamfer_mesh_step':0.2,
 'button_diameter':8.0,
 'button_guide_hole':8.6,
 'button_flange_diameter':10.4,
 'button_flange_cavity':11.0,
 'button_guide_outer_diameter':14.0,
 'button_guide_depth':3.0,
 'button_flange_thickness':1.2,
 'button_protrusion_at_outer_stop':1.2,
 'button_axial_allowance_at_outer_stop':0.4,
 'button_contact_pin_diameter':3.0,
 'button_face_dimple_diameter':3.6,
 'button_face_dimple_depth':0.3,
 'screw_head_well_diameter':7.0,
 'speaker_through_opening_diameter':14.5,
 'antenna_tab_center':[-39.0,46.0],
 'antenna_tab_radius':8.0,
 'antenna_trial_hole_diameter':6.5,
 'antenna_clamping_land_thickness':2.4,
 'antenna_rear_counterbore_diameter':11.6,
}
D=make_design()
JOIN=round(D['join']-D['seat'],8) # 1.8 above underside; preserves original seat allowance
BASE_TOP=JOIN+ORIGINAL_PARAMS['front_frame_thickness'] # original screw bearing plane
ROOF_BOTTOM=P['pcb_underside_to_screen_top']+P['screen_clearance']
ROOF_TOP=ROOF_BOTTOM+P['roof_thickness']
GUIDE_BOTTOM=ROOF_BOTTOM-P['button_guide_depth']
FLANGE_BOTTOM=ROOF_BOTTOM-P['button_flange_thickness']
CAP_TOP=ROOF_TOP+P['button_protrusion_at_outer_stop']
SCREEN_REFERENCE_CENTER=(-0.04,-7.99)  # Original footprint reference, not moved by the cutout change.
SCREEN_LEFT=-26.04  # Keep the left edge fixed; V8.1 moves the right edge inward 8.5 mm.
SCREEN_CENTER=(SCREEN_LEFT+P['screen_aperture_width']/2,-7.99)
BUTTONS={'LEFT':(-62.0,0.0),'UP':(-53.0,8.0),'DOWN':(-53.0,-8.0),
 'RIGHT':(-44.0,0.0),'B':(54.8,-9.7),'A':(61.0,3.0)}
SPEAKER=(-47.5,-24.0) # LS1 (102.5,124), footprint outer circle radius 6.25


def translated(g,xy):return affinity.translate(g,*xy)
def rr_center(x,y,w,h,r=0.8):return round_box(x-w/2,y-h/2,x+w/2,y+h/2,r)
SCREW_HOLES=unary_union([circle(x,y,ORIGINAL_PARAMS['screw_clearance_diameter']/2) for x,y in D['lugs']])
SCREW_WELLS=unary_union([circle(x,y,P['screw_head_well_diameter']/2) for x,y in D['lugs']])
BASE=D['front'].difference(SCREW_HOLES)
WALL=D['front'].difference(SCREW_WELLS)
TAB=circle(*P['antenna_tab_center'],P['antenna_tab_radius'])
TAB_NUT=circle(*P['antenna_tab_center'],P['antenna_rear_counterbore_diameter']/2)
TAB_NECK=TAB.difference(TAB_NUT)
ANT_HOLE=circle(*P['antenna_tab_center'],P['antenna_trial_hole_diameter']/2)
# Keep entire ears open rather than guessing SAO body height or LED light-pipe lengths.
EAR_WINDOWS=unary_union([
 D['pcb'].buffer(-0.8).intersection(box(-100,15,-27,70)),
 D['pcb'].buffer(-0.8).intersection(box(27,15,100,70))])
LANYARD=LineString([(-5,22.5),(5,22.5)]).buffer(4.0,quad_segs=24)
SPEAKER_HOLE=circle(*SPEAKER,P['speaker_through_opening_diameter']/2)
# Service windows open to lower edge above the retained original 2.4 mm interface.
POWER=native_box(139,131,161,150)
BOOT_RESET=native_box(174,129,201,152)
# J3 1x5: native pitch 2.54 along local Y, rotated 54 degrees in KiCad.
a=np.array([87.258061,126.014051]); b=a+10.16*np.array([math.sin(math.radians(54)),math.cos(math.radians(54))])
SPI=LineString([(a[0]-150,100-a[1]),(b[0]-150,100-b[1])]).buffer(3.0,quad_segs=24)
SERVICE=unary_union([POWER,BOOT_RESET,SPI])
NONBUTTON_OPEN=unary_union([EAR_WINDOWS,LANYARD,SPEAKER_HOLE,SERVICE])
HOLES=unary_union([circle(x,y,P['button_guide_hole']/2) for x,y in BUTTONS.values()])
CAVITIES=unary_union([circle(x,y,P['button_flange_cavity']/2) for x,y in BUTTONS.values()])
COLLARS=unary_union([circle(x,y,P['button_guide_outer_diameter']/2) for x,y in BUTTONS.values()]).difference(CAVITIES)


def screen_hole(extra=0.0):
 return rr_center(*SCREEN_CENTER,P['screen_aperture_width']+2*extra,P['screen_aperture_height']+2*extra,0.8+extra)


def lid_layers(antenna_hole:bool):
 tab_start=ROOF_TOP-P['antenna_clamping_land_thickness']
 zs=sorted(set([JOIN,BASE_TOP,GUIDE_BOTTOM,tab_start,ROOF_BOTTOM,
  ROOF_TOP-P['screen_chamfer_height'],ROOF_TOP]+[
  round(ROOF_TOP-P['screen_chamfer_height']+i*P['chamfer_mesh_step'],6)
  for i in range(1,round(P['screen_chamfer_height']/P['chamfer_mesh_step']))]))
 ls=[]
 for z0,z1 in zip(zs,zs[1:]):
  mid=(z0+z1)/2
  if mid<BASE_TOP:
   g=BASE
  else:
   g=WALL.difference(SERVICE)
   if mid>=GUIDE_BOTTOM:g=unary_union([g,COLLARS,TAB_NECK])
   if mid>=tab_start:g=unary_union([g,TAB])
   if mid>=ROOF_BOTTOM:
    extra=max(0.0,mid-(ROOF_TOP-P['screen_chamfer_height']))*P['screen_chamfer_width']/P['screen_chamfer_height']
    roof=unary_union([D['outer'],TAB]).difference(unary_union([NONBUTTON_OPEN,HOLES,SCREW_WELLS,screen_hole(extra)]))
    g=unary_union([g,roof])
   if antenna_hole:g=g.difference(ANT_HOLE)
  if not g.is_valid:raise ValueError('Invalid lid section')
  ls.append((z0,z1,g))
 return ls


def cap_layers(axial_allowance:float):
 tip=P['pcb_underside_to_unpressed_button_top']+axial_allowance
 if tip>=FLANGE_BOTTOM:raise ValueError('No contact pin length')
 pin=circle(0,0,P['button_contact_pin_diameter']/2)
 flange=circle(0,0,P['button_flange_diameter']/2)
 head=circle(0,0,P['button_diameter']/2)
 dimple=circle(0,0,P['button_face_dimple_diameter']/2)
 return [(tip,FLANGE_BOTTOM,pin),(FLANGE_BOTTOM,ROOF_BOTTOM,flange),
  (ROOF_BOTTOM,CAP_TOP-P['button_face_dimple_depth'],head),
  (CAP_TOP-P['button_face_dimple_depth'],CAP_TOP,head.difference(dimple))]


def coupon_layers():
 outer=rr_center(0,0,17,17,2)
 return [(0,3,outer.difference(circle(0,0,P['button_flange_cavity']/2))),
 (3,5,outer.difference(circle(0,0,P['button_guide_hole']/2)))]


def test_arm_layers():
 # A small left-button test bracket fitted to the existing left external lug.
 # One screw only: light testing, not a standalone rugged enclosure.
 lug=D['lugs'][0]; button=BUTTONS['LEFT']
 region=unary_union([circle(*lug,5.0),circle(*button,7.6)]).convex_hull
 base=D['front'].intersection(region).difference(SCREW_HOLES)
 walls=base.difference(SCREW_WELLS)
 collar=circle(*button,P['button_guide_outer_diameter']/2).difference(circle(*button,P['button_flange_cavity']/2))
 roof=region.difference(SCREW_WELLS).difference(circle(*button,P['button_guide_hole']/2))
 return [(JOIN,BASE_TOP,base),(BASE_TOP,GUIDE_BOTTOM,walls),
 (GUIDE_BOTTOM,ROOF_BOTTOM,unary_union([walls,collar])),(ROOF_BOTTOM,ROOF_TOP,roof)]


def to_print(m:trimesh.Trimesh, face_down:bool=True):
 n=m.copy()
 if face_down:n.apply_transform(trimesh.transformations.rotation_matrix(math.pi,[1,0,0]))
 n.apply_translation(-n.bounds[0])
 return n


def add_scad_module(name:str,layers:list,parts:list[str]):
 body=[]
 for z0,z1,g in layers:
  body.append(f'translate([0,0,{z0:.6f}]) linear_extrude(height={z1-z0:.6f}) {{ {scad_polygon(g)} }}')
 parts.append('module '+name+'(){ union(){\n'+'\n'.join(body)+'\n}}\n')


def validate_file(m:trimesh.Trimesh, path:Path)->dict[str,Any]:
 m.export(path)
 check=trimesh.load_mesh(path,process=True)
 if not(check.is_watertight and check.is_winding_consistent and check.volume>0 and len(check.split(only_watertight=False))==1):
  raise ValueError(f'Failed mesh checks: {path.name}')
 export_3mf({path.stem:m},path.with_suffix('.3mf'))
 c3=trimesh.load(path.with_suffix('.3mf'),force='mesh')
 if not c3.is_watertight or not np.allclose(c3.bounds,check.bounds,atol=1e-4):raise ValueError('3MF roundtrip failed')
 return {'watertight':True,'consistent_winding':True,'positive_volume':True,'connected_solids':1,
  'dimensions_mm':check.extents.tolist(),'volume_cm3':float(check.volume/1000),'triangles':len(check.faces),
  'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'STL_and_3MF_reimport':'passed'}


def collision_volume(layers_a,layers_b,xy=(0,0),z_offset=0.0):
 volume=0.0
 for a0,a1,ga in layers_a:
  for b0,b1,gb in layers_b:
   h=min(a1,b1+z_offset)-max(a0,b0+z_offset)
   if h>1e-8:volume+=h*ga.intersection(translated(gb,xy)).area
 return volume


def main():
 t=time.time();scad=[];report={};assembly={};prints={}
 jobs={
  'faceplate_SMA6p5_TRIAL':(lid_layers(True),'parts',True),
  'faceplate_antenna_tab_BLANK':(lid_layers(False),'parts',True),
  'button_cap_nominal_0p4':(cap_layers(0.4),'parts',True),
  'button_cap_shorter_0p6':(cap_layers(0.6),'tests',True),
  'button_slide_coupon':(coupon_layers(),'tests',True),
  'left_button_height_test':(test_arm_layers(),'tests',True),
 }
 for name,(layers,sub,fd) in jobs.items():
  print('Generating',name,flush=True)
  m=layered_mesh(layers);assembly[name]=m
  pr=to_print(m,fd);prints[name]=pr
  report[name]=validate_file(pr,ROOT/sub/(name+'.stl'))
  m.export(ROOT/'preview'/(name+'_ASSEMBLY_COORDS_DO_NOT_PRINT.stl'))
  add_scad_module(name,layers,scad)
  print(name,report[name]['dimensions_mm'],round(report[name]['volume_cm3'],3),'cm3',flush=True)
 # Collision tests include travel, but not a claimed safe travel specification for the switch.
 collisions={}
 for variant in [True,False]:
  label='SMA_trial' if variant else 'blank'
  for key,xy in BUTTONS.items():
   for dz in [0,-0.2,-0.4,-0.6,-0.9]:
    v=collision_volume(lid_layers(variant),cap_layers(.4),xy,dz)
    if v>1e-5:raise ValueError(f'Cap/lid collision {label} {key} {dz}: {v}')
  collisions[label]='No cap/lid volume overlap at offsets 0, -0.2, -0.4, -0.6, -0.9 mm. Not switch travel validation.'
 # Verify no change to the original contact/screw interface for the entire first 2.4 mm.
 interface_error=lid_layers(True)[0][2].symmetric_difference(BASE).area
 assert interface_error<1e-8
 # Reference PCB is only the outline/holes, not a complete electrical assembly.
 pcb=layered_mesh([(0,ORIGINAL_PARAMS['pcb_thickness'],D['pcb_reference'])])
 pcb.export(ROOT/'preview'/'pcb_reference_ASSEMBLY_COORDS_DO_NOT_PRINT.stl')
 # Generic print layout: select your own printer, supports and material.
 combined={'Faceplate SMA trial - verify connector before printing':prints['faceplate_SMA6p5_TRIAL'].copy()}
 row_y=float(combined[next(iter(combined))].extents[1])+7
 for i,key in enumerate(['LEFT','UP','DOWN','RIGHT','B','A']):
  m=prints['button_cap_nominal_0p4'].copy();m.apply_translation([4+i*16,row_y,0]);combined['Cap '+key+' nominal 0.4 mm allowance']=m
 export_3mf(combined,ROOT/'CatBadge_v03_Faceplate_and_6_Caps.3mf')
 all_comb=trimesh.load(ROOT/'CatBadge_v03_Faceplate_and_6_Caps.3mf',force='scene')
 assert len(all_comb.geometry)==7
 # Include the small slide test and one cap as a separately arranged print.
 cp=prints['button_cap_nominal_0p4'].copy();cp.apply_translation([22,0,0])
 export_3mf({'Button slide coupon':prints['button_slide_coupon'],'One nominal cap':cp},ROOT/'tests'/'PRINT_FIRST_button_slide_test.3mf')
 cp=prints['button_cap_nominal_0p4'].copy();cp.apply_translation([prints['left_button_height_test'].extents[0]+6,0,0])
 export_3mf({'Left lug height-test arm':prints['left_button_height_test'],'One nominal cap':cp},ROOT/'tests'/'PRINT_SECOND_left_button_height_test.3mf')
 # All editable dimensions are in this Python generator. OpenSCAD is generated geometry.
 head='''// CatBadge faceplate v0.3. Units mm. Unprinted prototype.\n// Modules are in assembly coordinates, PCB underside Z=0.\n// For printing, use supplied STLs/3MFs already oriented face-down.\n// Edit generate_faceplate.py to change dimensions; this is generated geometry.\npart="faceplate_SMA6p5_TRIAL";\n'''
 sel='\n'.join(('if' if i==0 else 'else if')+f'(part=="{name}") {name}();' for i,name in enumerate(jobs))
 (ROOT/'source'/'faceplate_v03.scad').write_text(head+'\n'.join(scad)+sel+'\n')
 measurements={
  'version':'0.3','status':'unprinted faceplate/cap prototype; user reports original v0.1 tray/frame fits perfectly',
  'datum':'bottom surface of main green PCB is Z=0; NOT bottom of case, solder pins or battery holder',
  'user_measurements_mm':{k:P[k] for k in list(P)[:3]},
  'chosen_design_parameters_mm':P,'derived':{'original_front_mating_plane':JOIN,'original_screw_head_bearing_plane':BASE_TOP,
   'roof_underside':ROOF_BOTTOM,'roof_top':ROOF_TOP,'cap_top_at_outer_stop':CAP_TOP,'cap_tip_at_outer_stop':7.2,
   'screen_nominal_clearance':.7,'screen_clearance_with_original_0p2_PCB_float':.5,
   'cap_nominal_axial_allowance_at_outer_stop':.4,'cap_allowance_with_original_0p2_PCB_float':.2,
   'screen_minus_button_top':3.7,'housing_BOTTOM_to_button_top':2.81,
   'NOTE':'2.81 is NOT switch travel, not metal housing top, and not the required contact-pin length.',
   'nominal_contact_pin_length':FLANGE_BOTTOM-7.2,'replacement_faceplate_height':ROOF_TOP-JOIN,
   'assembled_case_depth_excluding_caps_and_antenna':D['seat']+ROOF_TOP},
  'screen_center_mechanical_xy':SCREEN_CENTER,'button_centers_mechanical_xy':BUTTONS,
  'speaker_center_mechanical_xy':SPEAKER,'lug_centers_mechanical_xy':D['lugs'],
  'sources':[
   'User caliper measurements supplied 2026-09-08.',
   'Original CatBadge_Case_v0_1.zip supplied in this conversation; build_case.py and meshing utility reused.',
   'https://raw.githubusercontent.com/RetiaLLC/DefconBadge2026/main/hardware/kicad/2024_def_con_badge_v1.kicad_pcb',
   'Public KiCad inspected through web on 2026-09-08; U3 User.6 active rectangle and LS1 placement transcribed. Complete upstream STEP assembly NOT loaded.'
  ],
  'mechanical_source_details':{'U3_native_origin':[191.4,107.99],'U3_active_rectangle_local':[[-65.92,-18.36],[-16.96,18.36]],
   'U3_module_FFab_local':[[-75.18,-21.36],[2,21.36]],'LS1_native_position':[102.5,124],'LS1_silkscreen_radius':6.25},
  'limitations':[
   'Speaker height unknown: full through-opening, not a grille.',
   'Screen XY from footprint, not a measured actual display/glass bounding box; check all four image edges.',
   'Antenna connector not selected: 6.5 mm trial hole and blank tab offered, not universal SMA/RP-SMA/MMCX compatibility.',
   'Antenna tab hole axis points out of the front face, NOT upward in the PCB plane; articulated/right-angle antenna or fitting needed to point upward.',
   'Button caps float; nominal allowance is at the outer flange stop. Gravity can let a cap rest lightly on its switch.',
   'Switch travel/force/overtravel unknown; test with light pressure. No certified overtravel protection.',
   'No complete component interference, RF, thermal, drop, or load-bearing validation.',
   'No spring-antenna notch. Do not force the lid over an interfering spring.',
   'New 7 mm screw wells accept only screw heads/drivers that actually fit. Bearing plane unchanged; verify before reusing hardware.'
  ]
 }
 (ROOT/'source'/'design_data_v03.json').write_text(json.dumps(measurements,indent=2))
 tests={'status':'digital checks only; no physical printing or full all-component assembly test',
  'mesh_checks':report,'original_contact_interface_symmetric_difference_mm2':interface_error,
  'original_contact_interface_height_preserved':2.4,'button_lid_clearance_tests':collisions,
  'antenna_hole_center_distance_to_PCB_outline_mm':Point(P['antenna_tab_center']).distance(D['pcb']),
  'combined_3mf_object_count':len(all_comb.geometry),'elapsed_seconds':round(time.time()-t,2)}
 (ROOT/'validation_report.json').write_text(json.dumps(tests,indent=2))
 # Save lightweight geometries for the preview script; no internet dependencies.
 (ROOT/'source'/'preview_data.json').write_text(json.dumps({'outline':mapping(D['pcb']),'roof_outer':mapping(unary_union([D['outer'],TAB])),
  'screen_window':mapping(screen_hole()),'ear_windows':mapping(EAR_WINDOWS),'speaker_hole':mapping(SPEAKER_HOLE),
  'lanyard':mapping(LANYARD),'service_windows':mapping(SERVICE),'screw_wells':mapping(SCREW_WELLS),
  'button_holes':mapping(HOLES),'antenna_hole':mapping(ANT_HOLE),'parameters':measurements}))
 print('DONE',tests['elapsed_seconds'],'seconds',flush=True)

if __name__=='__main__':main()
