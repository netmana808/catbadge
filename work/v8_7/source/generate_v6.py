#!/usr/bin/env python3
"""CatBadge v6: side bulkhead mount and slip-on gamepad-style button caps.
Datum Z=0: UNDERSIDE of main PCB. Geometry only; unprinted prototype.
Run from Python 3.10+ with numpy, shapely>=2.1 and trimesh installed.
"""
from __future__ import annotations
import sys, math, json, time, shutil, subprocess, io
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Point, LineString, Polygon, box, MultiPoint
from shapely.ops import unary_union
import v03_reference as v
from mesh_tools import layered_mesh, export_3mf
import battery_cover as battery

ROOT=Path(__file__).resolve().parent.parent
P={
 'button_head_diameter':10.0, 'guide_bore_diameter':10.6,
 'guide_outer_diameter':14.0, 'socket_boss_diameter':4.8,
 'socket_depth':1.5, 'socket_trials':[3.0,3.1,3.2,3.3],
 'tall_head_bottom':9.4, 'tall_head_top':14.4,
 'low_head_bottom':6.8, 'low_head_top':8.8,
 'dimple_diameter':0.0, 'dimple_depth':0.0,
 'screen_bevel_width':0.0, 'antenna_roof_angle_degrees':45.0,
 'antenna_hole_diameter':6.5, 'antenna_axis_z':8.0,
 'antenna_outer_plane':2.2, 'antenna_inner_plane':-0.2,
 'antenna_land_width':10.5, 'antenna_land_z0':2.8, 'antenna_land_z1':13.2,
 'side_hole_radial_segments':128,
 'retainer_centres_x':[-17.0,17.0], 'retainer_width':5.0,
 'retainer_edge_overlap':1.2, 'retainer_root_overlap':2.0,
 'continuous_screw_lug_index':3,
}
# Locate a planar seat tangent to the inner slope of the upper-left ear.
d=v.D['pcb'].exterior.project(Point(-39,37))
C=np.array(v.D['pcb'].exterior.interpolate(d).coords[0])
T=np.array(v.D['pcb'].exterior.interpolate(d+.3).coords[0])-np.array(v.D['pcb'].exterior.interpolate(d-.3).coords[0]); T/=np.linalg.norm(T)
N=np.array([T[1],-T[0]])
assert not v.D['pcb'].contains(Point(C+N))

def slab(t0,t1,n0,n1):
 return Polygon([C+t*T+n*N for t,n in [(t0,n0),(t1,n0),(t1,n1),(t0,n1)]])
LAND_OUT=slab(-P['antenna_land_width']/2,P['antenna_land_width']/2,P['antenna_outer_plane'],10)
LAND_IN=slab(-P['antenna_land_width']/2,P['antenna_land_width']/2,-10,P['antenna_inner_plane'])
BHOLES=unary_union([v.circle(x,y,P['guide_bore_diameter']/2) for x,y in v.BUTTONS.values()])
COLLARS=unary_union([v.circle(x,y,P['guide_outer_diameter']/2) for x,y in v.BUTTONS.values()]).difference(BHOLES)
PROTECTED_LUGS=unary_union([v.circle(x,y,v.ORIGINAL_PARAMS['lug_radius']) for x,y in v.D['lugs']])
LOWER_BAR_CUT=unary_union([v.POWER,v.BOOT_RESET]).difference(PROTECTED_LUGS)

def lower_screw_tube(z):
 # Restore the circumferential wall removed by the boot/reset service cut.
 # Preserve the existing bearing plane, through bore and head recess.
 x,y=v.D['lugs'][P['continuous_screw_lug_index']]
 bore=v.ORIGINAL_PARAMS['screw_clearance_diameter'] if z<v.BASE_TOP else v.P['screw_head_well_diameter']
 return v.circle(x,y,v.ORIGINAL_PARAMS['lug_radius']).difference(v.circle(x,y,bore/2))

def screw_tube_coupon_layers():
 return [(v.JOIN,v.BASE_TOP,lower_screw_tube(v.JOIN)),
         (v.BASE_TOP,v.ROOF_TOP,lower_screw_tube(v.BASE_TOP))]

def retaining_ribs(overlap):
 # Two narrow lower-edge strips; retain the original 0.2 mm PCB float.
 # The broader roof-backed root narrows toward the board, so it does not
 # create a new unsupported shelf in the face-down print orientation.
 strips=unary_union([box(x-P['retainer_width']/2,-60,x+P['retainer_width']/2,-30) for x in P['retainer_centres_x']])
 return v.D['outer'].difference(v.D['pcb'].buffer(-overlap)).intersection(strips)

def revise_lid_profile(profile,z):
 overlap=P['retainer_edge_overlap'] if z<v.BASE_TOP else P['retainer_root_overlap']
 return unary_union([profile.difference(LOWER_BAR_CUT),retaining_ribs(overlap),lower_screw_tube(z)])

def lid_layers():
 zs=[v.JOIN,v.BASE_TOP,v.GUIDE_BOTTOM,v.ROOF_BOTTOM,v.ROOF_TOP-1,v.ROOF_TOP,P['antenna_land_z0'],P['antenna_land_z1']]
 zs += list(np.arange(v.ROOF_TOP-1,v.ROOF_TOP+.001,.2))
 zs=sorted(set(round(float(z),6) for z in zs if v.JOIN<=z<=v.ROOF_TOP))
 ls=[]
 for z0,z1 in zip(zs,zs[1:]):
  mid=(z0+z1)/2
  if mid<v.BASE_TOP:g=v.BASE
  else:
   g=v.WALL.difference(v.SERVICE)
   if mid>=v.GUIDE_BOTTOM:g=unary_union([g,COLLARS])
   if mid>=v.ROOF_BOTTOM:
    extra=P['screen_bevel_width']*max(0.0,mid-(v.ROOF_TOP-1))
    roof=v.D['outer'].difference(unary_union([v.NONBUTTON_OPEN,BHOLES,v.SCREW_WELLS,v.screen_hole(extra)]))
    g=unary_union([g,roof])
  if P['antenna_land_z0']<=mid<=P['antenna_land_z1']:
   g=g.difference(unary_union([LAND_OUT,LAND_IN]))
  ls.append((z0,z1,revise_lid_profile(g,mid)))
 return ls

def retaining_coupon_layers():
 # One short section reproduces the actual PCB edge, pad height and rib root.
 x=P['retainer_centres_x'][0]
 region=box(x-P['retainer_width']/2,-60,x+P['retainer_width']/2,-30)
 return [(a,b,poly.intersection(region)) for a,b,poly in lid_layers()]


def antenna_profile():
 # The lid prints face-down: assembly -Z points UP in print coordinates.
 # Enclose the original 128-segment circular clearance in a tangent 45-degree roof.
 r=P['antenna_hole_diameter']/2
 points=[(r*math.cos(i*2*math.pi/P['side_hole_radial_segments']),r*math.sin(i*2*math.pi/P['side_hole_radial_segments'])) for i in range(P['side_hole_radial_segments'])]
 return MultiPoint(points+[(0,-r*math.sqrt(2))]).convex_hull

def hole_scad(body):
 mat=[[float(T[0]),0,float(N[0]),float(C[0])],
      [float(T[1]),0,float(N[1]),float(C[1])],
      [0,1,0,P['antenna_axis_z']],[0,0,0,1]]
 return 'difference(){\n'+body+'\nmultmatrix('+json.dumps(mat)+') linear_extrude(height=30,center=true) {'+v.scad_polygon(antenna_profile())+'}\n}\n'

def cap_layers(diameter,tall=True):
 tip=v.P['pcb_underside_to_unpressed_button_top']
 bottom=tip-P['socket_depth']
 head0=P['tall_head_bottom'] if tall else P['low_head_bottom']
 head1=P['tall_head_top'] if tall else P['low_head_top']
 boss=v.circle(0,0,P['socket_boss_diameter']/2)
 socket=v.circle(0,0,diameter/2)
 head=v.circle(0,0,P['button_head_diameter']/2)
 # Small chamfer at the pocket entry, not an interference-fit barb.
 ls=[(bottom,bottom+.2,boss.difference(v.circle(0,0,diameter/2+.15))),
     (bottom+.2,tip,boss.difference(socket))]
 if head0>tip:ls.append((tip,head0,boss))
 ls.append((head0,head1,head))  # Flat print-bed face: no recessed-face bridge.
 return ls

def test_arm_layers():
 lug=v.D['lugs'][0]; button=v.BUTTONS['LEFT']
 region=unary_union([v.circle(*lug,5),v.circle(*button,7.8)]).convex_hull
 base=v.D['front'].intersection(region).difference(v.SCREW_HOLES)
 wall=base.difference(v.SCREW_WELLS)
 collar=v.circle(*button,P['guide_outer_diameter']/2).difference(v.circle(*button,P['guide_bore_diameter']/2))
 roof=region.difference(v.SCREW_WELLS).difference(v.circle(*button,P['guide_bore_diameter']/2))
 return [(v.JOIN,v.BASE_TOP,base),(v.BASE_TOP,v.GUIDE_BOTTOM,wall),
         (v.GUIDE_BOTTOM,v.ROOF_BOTTOM,unary_union([wall,collar])),(v.ROOF_BOTTOM,v.ROOF_TOP,roof)]

def coupon_layers():
 return [(0,P['antenna_outer_plane']-P['antenna_inner_plane'],v.round_box(-8,-7,8,7,1).difference(v.affinity.scale(antenna_profile(),xfact=1,yfact=-1,origin=(0,0))))]

def screen_coupon_layers():
 # Full-size aperture with the same straight aperture and 2 mm roof as the lid.
 # It checks the hole envelope only, not installation height or component fit.
 x0,y0,x1,y1=v.screen_hole().bounds
 outer=v.round_box(x0-3,y0-3,x1+3,y1+3,1.5)
 return [(a,b,outer.difference(v.screen_hole(P['screen_bevel_width']*max(0,(a+b)/2-(v.ROOF_TOP-1)))))
         for a,b,_ in lid_layers() if a>=v.ROOF_BOTTOM]

def m4_nut_holes():
 q=v.ORIGINAL_PARAMS
 radius=q['nut_across_flats']/math.sqrt(3)
 return unary_union([Polygon([(x+radius*math.cos(math.radians(30+60*i)),y+radius*math.sin(math.radians(30+60*i))) for i in range(6)]) for x,y in v.D['lugs']])

def rear_tray_layers():
 return battery.rear_layers(v.SCREW_HOLES,m4_nut_holes())

def m4_coupon_layers():
 # A small 10 mm lug reproduces the actual minimum wall around the nut pocket.
 x,y=v.D['lugs'][0]
 outer=v.circle(x,y,v.ORIGINAL_PARAMS['lug_radius'])
 holes=v.SCREW_HOLES;nuts=m4_nut_holes();depth=v.ORIGINAL_PARAMS['nut_recess_depth']
 return [(0,depth,outer.difference(nuts).difference(holes)),(depth,depth+2,outer.difference(holes))]

def emit(name,ls,folder='parts'):
 print('Building',name,flush=True)
 if name=='rear_tray_M4':
  # The new pocket intersects the old curved rim. Union independently meshed
  # sections to avoid ambiguous shared edges in the legacy layered mesher.
  sections=[]
  for a,b,poly in ls:
   pieces=[poly] if poly.geom_type=='Polygon' else list(poly.geoms)
   sections.extend(layered_mesh([(a,b,p)]) for p in pieces if p.area>1e-8)
  m=trimesh.boolean.union(sections,engine='manifold')
  expected=sum((b-a)*poly.area for a,b,poly in ls)
  assert abs(m.volume-expected)<.02,'Rear Boolean union changed volume'
  m=stl_stable(m)
 else:m=layered_mesh(ls)
 m.export(ROOT/'preview'/(name+'_ASSEMBLY.stl'))
 if name in ['rear_tray_M4','PRINT_FIRST_M4_lug_nut_test','battery_cover','PRINT_FIRST_cover_tab','PRINT_FIRST_cover_slot','PRINT_FIRST_cover_nut_post']:
  pr=v.to_print(m,False)
 elif name=='SMA_6p5_TEARDROP_panel_test':
  pr=m.copy();pr.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]));pr.apply_translation(-pr.bounds[0])
 else:pr=v.to_print(m,True)
 if name=='rear_tray_M4':pr=stl_stable(pr)
 rep=v.validate_file(pr,ROOT/folder/(name+'.stl'))
 return m,pr,rep

def stl_stable(mesh):
 # Boolean triangulation can leave zero-area slivers after float32 STL welding.
 # Remove only collapsed faces, then enforce the normal solid/volume checks.
 before=mesh.volume
 m=trimesh.load_mesh(io.BytesIO(mesh.export(file_type='stl')),file_type='stl',process=True)
 m.update_faces(m.area_faces>1e-12);m.remove_unreferenced_vertices()
 assert m.is_watertight and m.is_winding_consistent and len(m.split(only_watertight=False))==1
 assert abs(m.volume-before)<.02
 return m

def main():
 started=time.time();reports={};prints={};assemblies={}
 jobs={
  'PRINT_FIRST_cover_slot':(battery.female_coupon(),'tests'),
  'PRINT_FIRST_cover_tab':(battery.male_coupon(),'tests'),
  'PRINT_FIRST_cover_nut_post':(battery.nut_coupon(),'tests'),
  'battery_cover':(battery.cover_layers(),'parts'),
  'PRINT_FIRST_full_screw_tube_test':(screw_tube_coupon_layers(),'tests'),
  'PRINT_FIRST_edge_retainer_test':(retaining_coupon_layers(),'tests'),
  'PRINT_FIRST_M4_lug_nut_test':(m4_coupon_layers(),'tests'),
  'rear_tray_M4':(rear_tray_layers(),'parts'),
  'PRINT_FIRST_screen61_fit_ring':(screen_coupon_layers(),'tests'),
  'faceplate_SIDE_BLANK':(lid_layers(),'parts'),
  'left_button_height_test_v6':(test_arm_layers(),'tests'),
  'SMA_6p5_TEARDROP_panel_test':(coupon_layers(),'tests'),
 }
 for dia in P['socket_trials']:
  label=f'{dia:.1f}'.replace('.','p')
  jobs[f'cap_SHORT_socket_{label}']=(cap_layers(dia,False),'tests')
  jobs[f'cap_TALL_socket_{label}']=(cap_layers(dia,True),'parts')
 for name,(ls,folder) in jobs.items():
  a,p,r=emit(name,ls,folder);assemblies[name]=a;prints[name]=p;reports[name]=r
  print(' ',r['triangles'],'triangles;',round(r['volume_cm3'],3),'cm3',flush=True)
 # Pointed side-hole roof: OpenSCAD subtracts the extruded teardrop profile.
 # The tested project-local OpenSCAD 2026.09.07 defaults to Manifold.
 cutter=ROOT/'source'/'cut_side_hole.scad'
 cutter.write_text(hole_scad('import("../preview/faceplate_SIDE_BLANK_ASSEMBLY.stl",convexity=20);'))
 holepath=ROOT/'preview'/'faceplate_SIDE6p5_TEARDROP_TRIAL_ASSEMBLY.stl'
 print('Cutting side hole with OpenSCAD',flush=True)
 run=subprocess.run(['openscad','-o',str(holepath),str(cutter)],capture_output=True,text=True,timeout=180)
 (ROOT/'source'/'openscad_build_log.txt').write_text(run.stdout+run.stderr)
 if run.returncode or not holepath.exists():raise RuntimeError('OpenSCAD cylinder subtraction failed: '+run.stderr)
 name='faceplate_SIDE6p5_TEARDROP_TRIAL'
 a=trimesh.load_mesh(holepath,process=True)
 p=v.to_print(a,True)
 reports[name]=v.validate_file(p,ROOT/'parts'/(name+'.stl'))
 assemblies[name]=a;prints[name]=p
 # Mechanical validation: exact mating-plane section and original fastener seats.
 assert lid_layers()[0][2].symmetric_difference(revise_lid_profile(v.BASE,v.JOIN+.01)).area<1e-8
 assert abs(P['antenna_outer_plane']-P['antenna_inner_plane']-2.4)<1e-9
 # Check all tall-cap diameters use identical external geometry. Test against
 # lid at measured rest height, 0.2 mm PCB float and selected depressions.
 for xy in v.BUTTONS.values():
  for off in [0,.2,-.2,-.5,-.8]:
   assert v.collision_volume(lid_layers(),cap_layers(3.2,True),xy,off)<1e-5,(xy,off)
 # Full kit: cap fit is NOT chosen for the user. 3.2 is a labelled trial only.
 full={'v6 lid - 61 mm screen toward A-B - SIDE 6.5 TEARDROP TRIAL':prints['faceplate_SIDE6p5_TEARDROP_TRIAL'].copy()}
 y=prints['faceplate_SIDE6p5_TEARDROP_TRIAL'].extents[1]+6
 for i,b in enumerate(v.BUTTONS):
  cp=prints['cap_TALL_socket_3p2'].copy();cp.apply_translation([4+14*i,y,0]);full['TRIAL tall cap 3.2 socket 4.8 stem '+b]=cp
 export_3mf(full,ROOT/'CatBadge_v6_Side_Mount_and_6_TRIAL_Caps.3mf')
 assert len(trimesh.load(ROOT/'CatBadge_v6_Side_Mount_and_6_TRIAL_Caps.3mf',force='scene').geometry)==7
 # All printable case parts on one M5C-sized plate: lid, tray, six caps.
 combined={'v6 M4 lid - SCREEN61 - TEARDROP':prints['faceplate_SIDE6p5_TEARDROP_TRIAL'].copy()}
 tray=prints['rear_tray_M4'].copy()
 tray_y=combined[next(iter(combined))].extents[1]+6
 tray.apply_translation([0,tray_y,0]);combined['v6 M4 rear tray - hex nut pockets']=tray
 cap_y=tray.bounds[1,1]+6
 for i,button in enumerate(v.BUTTONS):
  cp=prints['cap_TALL_socket_3p2'].copy();cp.apply_translation([4+14*i,cap_y,0])
  combined['v6 FLAT tall cap 3.2 TRIAL 4.8 stem '+button]=cp
 cover=prints['battery_cover'].copy();cover.apply_translation([prints['faceplate_SIDE6p5_TEARDROP_TRIAL'].extents[0]+6,0,0])
 combined['v6 detachable AA cover - 15.7 x 32.7 x 59.7 holder']=cover
 bounds=np.array([mesh.bounds for mesh in combined.values()])
 lo=bounds[:,0,:].min(axis=0);hi=bounds[:,1,:].max(axis=0)
 plate_offset=(np.array([220.,220.])-(hi-lo)[:2])/2-lo[:2]
 for mesh in combined.values():mesh.apply_translation([*plate_offset,0])
 export_3mf(combined,ROOT/'CatBadge_v6_ALL_PARTS_M4.3mf')
 # Keep test caps as individually named objects with positional mapping.
 trial={}
 for i,dia in enumerate(P['socket_trials']):
  key=f'cap_SHORT_socket_{dia:.1f}'.replace('.','p');m=prints[key].copy();m.apply_translation([14*i,0,0]);trial[f'SHORT socket {dia:.1f} mm']=m
 for i,dia in enumerate(P['socket_trials']):
  key=f'cap_TALL_socket_{dia:.1f}'.replace('.','p');m=prints[key].copy();m.apply_translation([14*i,15,0]);trial[f'TALL socket {dia:.1f} mm']=m
 arm=prints['left_button_height_test_v6'].copy();arm.apply_translation([63,0,0]);trial['LEFT screw-lug button-height test']=arm
 c=prints['SMA_6p5_TEARDROP_panel_test'].copy();c.apply_translation([63,25,0]);trial['ANTENNA coupon 6.5 TEARDROP 2.4 panel']=c
 export_3mf(trial,ROOT/'PRINT_FIRST_v6_Button_and_SMA_Test_Kit.3mf')
 assert len(trimesh.load(ROOT/'PRINT_FIRST_v6_Button_and_SMA_Test_Kit.3mf',force='scene').geometry)==10
 short={name:mesh for name,mesh in trial.items() if name.startswith('SHORT')}
 export_3mf(short,ROOT/'PRINT_FIRST_4_Short_Slip_On_Caps.3mf')
 pcb=layered_mesh([(0,1.6,v.D['pcb_reference'])]);pcb.export(ROOT/'preview'/'pcb_REFERENCE_ASSEMBLY.stl')
 nearest=min(np.linalg.norm(np.array(a)-np.array(b)) for i,a in enumerate(v.BUTTONS.values()) for j,b in enumerate(v.BUTTONS.values()) if i<j)
 data={
 'version':'6.0','battery_cover':battery.P,'rear_shell':{'outside_z_mm':battery.BACK,'floor_mm':battery.P['rear_floor'],'electronics_clearance_mm':8.0,'main_body_depth_mm':v.ROOF_TOP-battery.BACK,'covered_battery_depth_mm':v.ROOF_TOP-battery.COVER_OUTER_Z},'status':'unprinted prototype; original v0.1 rear tray only is user-fit-confirmed',
 'datum':'underside of the main PCB, NOT its front surface or underside of case',
 'user_measurements':{'screen_top_from_PCB_bottom':10.5,'button_top_from_PCB_bottom':6.8,'metal_housing_BOTTOM_from_PCB_bottom':3.99,'new_button_width':3.0,'new_button_height':4.0},
 'measurement_caveat':'The newer 4 mm height has no explicit datum and is NOT used to replace 6.8 mm assembly datum or set socket depth. Metal housing top and switch travel remain unknown.',
 'fasteners':{'thread':'M4','through_hole_diameter_mm':v.ORIGINAL_PARAMS['screw_clearance_diameter'],'nut_pocket_across_flats_mm':v.ORIGINAL_PARAMS['nut_across_flats'],'nut_pocket_depth_mm':v.ORIGINAL_PARAMS['nut_recess_depth'],'assumed_nut':'standard DIN934 hex, nominal 7 mm AF x 3.2 mm thick; not nyloc','head_well_diameter_unchanged_mm':7.0,'lug_centres_unchanged':v.D['lugs'],'combined_3mf':'CatBadge_v6_ALL_PARTS_M4.3mf'},
 'overhang_revision':{'screen_opening':'straight walls, 61 x 40 mm throughout roof','button_face':'flat; former 0.25 mm recess removed','antenna_profile':'6.5 mm inscribed circle plus 45 degree pointed roof; point toward print +Z','lower_bars':'power and boot/reset perimeter bridges removed through the mating rim','remaining':'screw-seat and SPI service bridges require slicer review'},
 'badge_retention':{'count':2,'centres_x_mm':P['retainer_centres_x'],'width_mm':P['retainer_width'],'PCB_edge_overlap_mm':P['retainer_edge_overlap'],'roof_root_overlap_mm':P['retainer_root_overlap'],'contact_face_assembly_z_mm':v.JOIN,'PCB_top_nominal_mm':v.ORIGINAL_PARAMS['pcb_thickness'],'nominal_float_mm':v.JOIN-v.ORIGINAL_PARAMS['pcb_thickness'],'status':'trial; verify bare edge clearance and physical fit','coupon':'tests/PRINT_FIRST_edge_retainer_test.3mf'},
 'lower_screw_mount':{'revision':'full circumferential tube wall beside boot/reset opening','centre_xy_mm':v.D['lugs'][P['continuous_screw_lug_index']],'outer_diameter_mm':10.0,'through_bore_mm':4.4,'head_recess_mm':7.0,'bearing_assembly_z_mm':v.BASE_TOP,'full_height_mm':v.ROOF_TOP-v.JOIN,'coupon':'tests/PRINT_FIRST_full_screw_tube_test.3mf'},
 'button_revision':{'outside_stem_diameter_mm':4.8,'previous_diameter_mm':5.4,'status':'trial interpretation of thinner attachment; no physical test','socket_diameters_and_engagement_unchanged':True},
 'screen_aperture':{'width_mm':v.P['screen_aperture_width'],'height_mm':v.P['screen_aperture_height'],'bounds_xy_mm':list(v.screen_hole().bounds),'fixed_edge':'left / four-button side','extension_mm_toward_AB':9.0,'coupon':'tests/PRINT_FIRST_screen61_fit_ring.3mf'},
 'parameters':P,'button_centres':v.BUTTONS,'screen_centre':v.SCREEN_CENTER,
 'antenna':{'pcb_edge_point_xy':C.tolist(),'tangent_xy':T.tolist(),'outward_axis_xy':N.tolist(),'axis_z':P['antenna_axis_z'],'hole_radial_segments':P['side_hole_radial_segments'],'outer_case_XY_profile_not_expanded':True,'panel_thickness':P['antenna_outer_plane']-P['antenna_inner_plane'],'exact_connector_not_selected':True},
 'caps':{'round_socket_assumption':True,'socket_engagement':P['socket_depth'],'short_cap_height':P['low_head_top']-(v.P['pcb_underside_to_unpressed_button_top']-P['socket_depth']),'tall_cap_height':P['tall_head_top']-(v.P['pcb_underside_to_unpressed_button_top']-P['socket_depth']),'tall_face_projection':P['tall_head_top']-v.ROOF_TOP,'head_guide_radial_clearance':(P['guide_bore_diameter']-P['button_head_diameter'])/2,'minimum_button_face_gap':float(nearest-P['button_head_diameter']),'caps_are_stem_mounted_not_flange_captive':True},
 'compatibility':'Replace v0.3 lid rather than enlarge its holes. Use the revised M4 rear tray; the old M3 tray is not an M4 assembly. New short caps can be tested on bare board or original open frame; tall caps are only for v6 lid.',
 'sources':['Earlier generated v0.3 package and original v0.1 design source from this conversation.','User dimension messages.','https://raw.githubusercontent.com/RetiaLLC/DefconBadge2026/main/hardware/kicad/2024_def_con_badge_v1.kicad_pcb'],
 'limits':['No physical print, button-return, load, RF, or complete component interference validation.','10.5 mm wide flat land, 2.4 mm panel and 6.5 mm trial hole must be checked against the selected connector, nut, washer and cable.','Assembly height measurement is retained; 4 mm new height is not assumed to be exposed actuator length.','Mating height and screw seats retained; mating profile changes at the two lower service bars and two retaining pads.','No spring-antenna notch. Intended external antenna arrangement must replace rather than parallel the original spring.']}
 (ROOT/'source'/'design_data_v6.json').write_text(json.dumps(data,indent=2))
 checks={'status':'digital mesh and selected geometric checks only', 'parts':reports,
 'mating_profile_revision':'two lower bars removed; two 1.2 mm PCB-edge-overlap pads added','screw_head_bearing_height_mm':v.BASE_TOP,
 'cap_to_lid_intersections_mm3':0,'cap_test_offsets_mm':[0,.2,-.2,-.5,-.8],
 'minimum_button_face_gap_mm':float(nearest-P['button_head_diameter']),'combined_3mf_object_count':7,'all_parts_3mf_object_count':9,'test_kit_object_count':10,
 'elapsed_seconds':round(time.time()-started,2)}
 (ROOT/'validation_report.json').write_text(json.dumps(checks,indent=2))
 # Editable layer-based OpenSCAD for the same geometry, separate module per part.
 scad=['// v6 generated geometry. Edit generate_v6.py for parameters. mm; PCB underside Z=0.','part="faceplate_SIDE6p5_TEARDROP_TRIAL";']
 for name,(ls,_) in jobs.items():v.add_scad_module(name,ls,scad)
 scad.append('module faceplate_SIDE6p5_TEARDROP_TRIAL(){'+hole_scad('faceplate_SIDE_BLANK();')+'}')
 jobs['faceplate_SIDE6p5_TEARDROP_TRIAL']=([], 'parts')
 scad+= [('if' if i==0 else 'else if')+f'(part=="{name}") {name}();' for i,name in enumerate(jobs)]
 (ROOT/'source'/'faceplate_v6.scad').write_text('\n'.join(scad))
 fit={}
 for i,key in enumerate(['PRINT_FIRST_cover_slot','PRINT_FIRST_cover_tab','PRINT_FIRST_cover_nut_post']):
  cp=prints[key].copy();cp.apply_translation([i*25,0,0]);fit[key]=cp
 export_3mf(fit,ROOT/'PRINT_FIRST_v6_Cover_Mount_Test.3mf')
 print('DONE',checks['elapsed_seconds'],'seconds',flush=True)

if __name__=='__main__':main()
