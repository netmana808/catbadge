#!/usr/bin/env python3
"""Generate a first-fit CatBadge enclosure from upstream KiCad Edge.Cuts.

Python 3.10+, numpy and shapely>=2.0 are required to generate OpenSCAD.
Run: python build_case.py
Then: openscad -o ../catbadge_rear_tray.stl -D 'part="tray"' catbadge_case.scad

The PCB curve control points and placements below were transcribed from the
public 2024_def_con_badge_v1.kicad_pcb in RetiaLLC/DefconBadge2026 on 2026-09-07.
They are not a photograph trace. No upstream complete 3-D assembly was loaded.
This is an UNPRINTED / UNFIT-TESTED prototype. Read ../README.md before assembly.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box, mapping
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import affinity

ROOT = Path(__file__).resolve().parent
SOURCE_URL = 'https://github.com/RetiaLLC/DefconBadge2026/blob/main/hardware/kicad/2024_def_con_badge_v1.kicad_pcb'
# These are engineering choices, not dimensions claimed by the badge manufacturer.
PARAMS = dict(
    pcb_thickness=1.6, radial_clearance=0.4, thickness_clearance=0.2,
    wall=2.4, floor=2.4, rear_component_clearance=8.0,
    retaining_overlap=0.8, ledge_thickness=0.8, ramp_step=0.2,
    front_frame_thickness=2.4, lug_radius=5.0, lug_edge_distance=5.3,
    screw_clearance_diameter=4.4, nut_across_flats=7.4, nut_recess_depth=3.4,
    fit_ring_height=1.2, fit_ring_wall=2.4, curve_tolerance=0.005,
)

# KiCad native XY, mm, Y down. Each entry is a line (2 points) or cubic Bezier (4).
# Only EXTERIOR Edge.Cuts, lines 40022-40203 in the upstream source as accessed.
EDGES = [
 [[149.977946,72.977139],[149.977946,72.977139],[134.164824,72.142181],[125.19235,77.035687]],
 [[83.4,86.6],[83.0,87.4]],
 [[174.763542,77.035687],[187.347202,61.602341],[197.2,59.4],[197.80754,59.024688]],
 [[102.156005,58.964313],[101.6,59.4],[91.02591,63.632439],[83.4,86.6]],
 [[199.92535,137.017162],[198.91736,137.0],[193.06652,141.817189],[149.983244,140.978837]],
 [[83.0,87.4],[83.192351,87.035687],[65.88997,125.3009],[100.030538,137.017162]],
 [[100.35019,137.082196],[101.038534,136.826278],[106.889371,141.817189],[149.983244,140.978837]],
 [[125.19235,77.035687],[112.379883,61.330967],[102.25765,58.989001],[102.156005,58.964313]],
 [[149.977946,72.977139],[149.977946,72.977139],[165.791068,72.142181],[174.763542,77.035687]],
 [[100.030538,137.017162],[100.35019,137.082196]],
 [[198.17784,59.167642],[197.80754,59.024688]],
 [[216.763539,87.035687],[216.763539,87.035687],[234.065919,125.3009],[199.92535,137.017162]],
 [[198.17784,59.167642],[198.17784,59.167642],[209.129979,63.632439],[216.763539,87.035687]],
]
PLACEMENTS = {
 'J7_USB_C': {'xy':[214,115.6],'rotation_deg':-105.945,'side':'back'},
 'J8_NeoPixel': {'xy':[85.9,115.2],'rotation_deg':-74.055,'side':'back'},
 'Card1_microSD': {'xy':[115,132],'rotation_deg':170.909,'side':'back'},
 'J4_UART': {'xy':[127.8,79.7],'rotation_deg':21.25,'side':'back'},
 'J6_QWIIC': {'xy':[172.1,79.7],'rotation_deg':-21.251,'side':'back'},
 'J1_UFL': {'xy':[107.47,66],'rotation_deg':180,'side':'back'},
 'J3_SPI': {'xy':[87.258061,126.014051],'rotation_deg':54,'side':'front'},
 'J5_SAO': {'xy':[187.872439,67.496906],'rotation_deg':-52,'side':'front'},
 'J9_battery': {'xy':[157.495,137.165],'rotation_deg':90,'side':'back',
     'footprint':'Battery:BatteryHolder_Keystone_2462_2xAA',
     'silkscreen_native_local_bounds':[-2.69,-24.055,57.02,9.065],
     'note':'33.12 x 59.71 mm silkscreen envelope, not measured installed housing'},
 'SW1_reset': {'xy':[193.25,134.1],'rotation_deg':9.09,'side':'front'},
 'SW2_boot': {'xy':[181.25,136.1],'rotation_deg':9.09,'side':'front'},
 'SW3_left': {'xy':[88,100],'rotation_deg':0,'side':'front'},
 'SW4_up': {'xy':[97,92],'rotation_deg':0,'side':'front'},
 'SW5_down': {'xy':[97,108],'rotation_deg':0,'side':'front'},
 'SW6_right': {'xy':[106,100],'rotation_deg':0,'side':'front'},
 'SW7_B': {'xy':[204.8,109.7],'rotation_deg':0,'side':'front'},
 'SW8_A': {'xy':[211,97],'rotation_deg':0,'side':'front'},
 'SW9_power': {'xy':[150,135.5],'rotation_deg':-90,'side':'front'},
 'U1_ESP32': {'xy':[178.595,103.85],'rotation_deg':180,'side':'back'},
}

def bezier_points(p: np.ndarray, tol: float, depth: int=0) -> list[list[float]]:
    """Adaptive de Casteljau subdivision, conservatively bounded by control hull."""
    chord = p[-1]-p[0]
    length = np.linalg.norm(chord)
    if length < 1e-10:
        flat = max(np.linalg.norm(p[1]-p[0]),np.linalg.norm(p[2]-p[0]))
    else:
        flat = max(abs(chord[0]*(p[i,1]-p[0,1])-chord[1]*(p[i,0]-p[0,0]))/length for i in [1,2])
    # Also bound deviations along the chord (a degenerate/backtracking Bezier).
    if flat <= tol and all(np.dot(q-p[0],chord) >= -tol*max(length,1) and np.dot(q-p[-1],chord) <= tol*max(length,1) for q in p[1:-1]):
        return [p[0].tolist(),p[-1].tolist()]
    if depth >= 24:
        raise ValueError('Bezier subdivision failed to converge')
    a=(p[0]+p[1])/2; b=(p[1]+p[2])/2; c=(p[2]+p[3])/2
    d=(a+b)/2; e=(b+c)/2; f=(d+e)/2
    return bezier_points(np.array([p[0],a,d,f]),tol,depth+1)[:-1] + bezier_points(np.array([f,e,c,p[3]]),tol,depth+1)

def get_outline() -> Polygon:
    remain = [np.array(e,dtype=float) for e in EDGES]
    ordered = [remain.pop(0)]
    while remain:
        tail=ordered[-1][-1]
        matches=[]
        for i,e in enumerate(remain):
            if np.linalg.norm(e[0]-tail)<1e-6: matches.append((i,False))
            if np.linalg.norm(e[-1]-tail)<1e-6: matches.append((i,True))
        if len(matches)!=1: raise ValueError(f'Non-unique board edge connection: {tail}, {matches}')
        i,rev=matches[0]; e=remain.pop(i)
        ordered.append(e[::-1] if rev else e)
    if np.linalg.norm(ordered[-1][-1]-ordered[0][0])>1e-6: raise ValueError('Open board outline')
    points=[]
    for edge in ordered:
        pts = edge.tolist() if len(edge)==2 else bezier_points(edge,PARAMS['curve_tolerance'])
        points.extend(pts[:-1])
    # Mechanical coordinates: origin (150,100) in the KiCad file, Y up.
    p=Polygon([(x-150,100-y) for x,y in points])
    if not p.is_valid or p.area < 5000: raise ValueError('Invalid or unexpectedly small board outline')
    return orient(p,sign=1)

def native_box(x0:float,y0:float,x1:float,y1:float) -> Polygon:
    return box(x0-150,100-y1,x1-150,100-y0)

def round_box(x0:float,y0:float,x1:float,y1:float,r:float=1.5):
    if min(x1-x0,y1-y0)<2*r: raise ValueError('Radius exceeds rectangle half size')
    return box(x0+r,y0+r,x1-r,y1-r).buffer(r,quad_segs=12)

def circle(x:float,y:float,r:float):
    return Point(x,y).buffer(r,quad_segs=24)

def checked(poly, label:str):
    if poly.is_empty or not poly.is_valid: raise ValueError(f'{label} is empty or invalid')
    return poly

def scad_polygon(g) -> str:
    if g.is_empty: return 'union(){}'
    polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
    parts=[]
    for poly in polys:
        poly=orient(poly,sign=1)
        points=[];paths=[]
        for ring in [poly.exterior,*poly.interiors]:
            coords=list(ring.coords)[:-1]
            paths.append(list(range(len(points),len(points)+len(coords))))
            points.extend([[round(x,6),round(y,6)] for x,y in coords])
        parts.append('polygon(points='+json.dumps(points,separators=(',',':'))+',paths='+json.dumps(paths,separators=(',',':'))+',convexity=12);')
    return 'union(){\n'+'\n'.join(parts)+'\n}'

def make_design() -> dict[str,Any]:
    p=get_outline(); q=PARAMS
    shell=p.buffer(q['radial_clearance']+q['wall'],quad_segs=16)
    lug_border=p.buffer(q['lug_edge_distance'],quad_segs=24)
    horizontal=lug_border.intersection(LineString([(-110,5),(110,5)]))
    lx,_,rx,_=horizontal.bounds
    lugs=[(lx,5),(rx,5)]
    for x in [-25,25]:
        line=lug_border.intersection(LineString([(x,-100),(x,100)]))
        lugs.append((x,line.bounds[1]))
    outer=checked(unary_union([shell]+[circle(x,y,q['lug_radius']) for x,y in lugs]),'outer')
    # Wide side access, intentionally not a tight cable-specific port fit.
    ports={
        'USB_C':native_box(201,103,240,129),
        'NeoPixel':native_box(60,103,98,128),
        'microSD':native_box(102,124,130,155),
        'UART':native_box(117,65,139,91),
        'QWIIC':native_box(161,65,183,91),
    }
    port_union=unary_union(list(ports.values()))
    # External fastener posts must survive wide port reliefs. In particular,
    # the microSD service region crosses one lower lug's XY envelope.
    protected_lugs=unary_union([circle(x,y,q['lug_radius']) for x,y in lugs]).difference(p.buffer(q['radial_clearance']))
    # Battery aperture uses the silkscreen XY envelope + clearance, not a guessed height.
    battery=native_box(131.5,79,168.5,141)
    battery=round_box(*battery.bounds,r=1.2)
    # Upper access to U.FL, UART/QWIIC and the stock lanyard opening. Leave a back rim.
    top_access=native_box(85,50,215,88).intersection(p.buffer(-1.2))
    vents=[]
    for x0,x1 in [(-51,-29),(29,51)]:
        for y in [-3,-10,-17]: vents.append(round_box(x0,y-1.2,x1,y+1.2,r=1.1))
    floor_openings=unary_union([battery,top_access,*vents])
    floor=checked(outer.difference(floor_openings),'floor')
    wall=checked(unary_union([outer.difference(p.buffer(q['radial_clearance'])).difference(port_union),protected_lugs]),'wall')
    # Relieve front edge overlap near the bottom boot/reset controls and SPI header.
    # Only the retaining lip is removed; the outside protective perimeter remains.
    front_reliefs=unary_union([
        native_box(174,129,201,149),
        native_box(80,120,105,140),
        native_box(140,131,160,147),
    ]).intersection(p.buffer(q['radial_clearance']))
    front_inner=unary_union([p.buffer(-q['retaining_overlap']),front_reliefs])
    front=checked(outer.difference(front_inner),'front')
    ring=checked(p.buffer(q['radial_clearance']+q['fit_ring_wall']).difference(p.buffer(q['radial_clearance'])),'fit ring')
    # Rear ledge is interrupted at actual ports and at the near-edge battery holder.
    seat=q['floor']+q['rear_component_clearance']
    join=seat+q['pcb_thickness']+q['thickness_clearance']
    ramp_height=q['radial_clearance']+q['retaining_overlap']
    ramp_start=seat-q['ledge_thickness']-ramp_height
    ramps=[]
    n=math.ceil(round(ramp_height/q['ramp_step'],8))
    for i in range(n):
        h=ramp_height/n
        inset=q['radial_clearance']-(i+1)*h
        section=unary_union([outer.difference(p.buffer(inset)).difference(port_union).difference(battery),protected_lugs])
        ramps.append((ramp_start+i*h,h,checked(section,f'ramp {i}')))
    ledge=checked(unary_union([outer.difference(p.buffer(-q['retaining_overlap'])).difference(port_union).difference(battery),protected_lugs]),'ledge')
    for label,section in [('floor',floor),('wall',wall),('ledge',ledge),('front',front),*[(f'ramp{i}',g) for i,(_,_,g) in enumerate(ramps)]]:
        for x,y in lugs:
            if not section.covers(circle(x,y,2.8)):
                raise ValueError(f'Fastener post removed by a relief in {label}')
    # Reference PCB geometry, NOT a printable case part.
    slot=LineString([(-4,22.5),(4,22.5)]).buffer(2.5,quad_segs=24)
    pcb_reference=p.difference(slot)
    for kx,ky in [(142.505,110),(157.495,110)]:
        pcb_reference=pcb_reference.difference(circle(kx-150,100-ky,1.65))
    return dict(pcb=p,outer=outer,ports=ports,floor=floor,wall=wall,front=front,ring=ring,
                battery=battery,top_access=top_access,ledges=ledge,ramps=ramps,
                seat=seat,join=join,ramp_start=ramp_start,lugs=lugs,pcb_reference=pcb_reference)

def main() -> None:
    q=PARAMS
    assert q['pcb_thickness']>0 and q['retaining_overlap']>q['radial_clearance']
    assert q['rear_component_clearance']>=4 and q['nut_recess_depth'] < q['floor']+q['rear_component_clearance']
    d=make_design(); bounds=d['outer'].bounds
    modules=[]
    for name,key in [('floor_2d','floor'),('wall_2d','wall'),('ledge_2d','ledges'),('front_2d','front'),('fit_ring_2d','ring'),('pcb_reference_2d','pcb_reference')]:
        modules.append(f'module {name}(){{\n{scad_polygon(d[key])}\n}}')
    for i,(_,_,g) in enumerate(d['ramps']): modules.append(f'module ramp_{i}_2d(){{{scad_polygon(g)}}}')
    lugs=json.dumps(d['lugs'])
    head=f'''// CatBadge edge-capture case v0.1 — UNPRINTED FIRST-FIT PROTOTYPE
// Source: {SOURCE_URL}
// Source PCB: 2024_def_con_badge_v1, inside the DefconBadge2026 repository.
// Units mm. No physical fit, drop, thermal, or RF certification.
// Regenerate geometry/clearances by editing PARAMS in build_case.py.
// Select: "tray", "front", "fit_ring", "pcb_reference", "assembly".
part = "tray";
$fn=72;
eps=0.005;
lugs={lugs};
seat={d['seat']};
join={d['join']};
frame_h={q['front_frame_thickness']};
module print_origin() {{translate([{ -bounds[0]},{ -bounds[1]},0]) children();}}
module screws(){{for(p=lugs) translate([p[0],p[1],-1]) cylinder(d={q['screw_clearance_diameter']},h=50);}}
module nut_recesses(){{for(p=lugs) translate([p[0],p[1],-eps]) rotate([0,0,30]) cylinder(d={q['nut_across_flats'] / math.cos(math.pi/6)},h={q['nut_recess_depth']}+eps,$fn=6);}}
'''
    tray=f'''module tray(){{difference(){{union(){{
  linear_extrude(height={q['floor']}) floor_2d();
  translate([0,0,{q['floor']}-eps]) linear_extrude(height={d['ramp_start']-q['floor']}+2*eps) wall_2d();
'''
    for i,(z,h,_) in enumerate(d['ramps']): tray+=f'  translate([0,0,{z}-eps]) linear_extrude(height={h}+2*eps) ramp_{i}_2d();\n'
    tray+=f'''  translate([0,0,{d['seat']-q['ledge_thickness']}-eps]) linear_extrude(height={q['ledge_thickness']}+eps) ledge_2d();
  translate([0,0,{d['seat']}-eps]) linear_extrude(height={d['join']-d['seat']}+eps) wall_2d();
}} screws(); nut_recesses();}}}}
module front(){{difference(){{linear_extrude(height=frame_h) front_2d();screws();}}}}
module fit_ring(){{linear_extrude(height={q['fit_ring_height']}) fit_ring_2d();}}
module pcb_reference(){{linear_extrude(height={q['pcb_thickness']}) pcb_reference_2d();}}
if(part=="tray") print_origin() tray();
else if(part=="front") print_origin() front();
else if(part=="fit_ring") print_origin() fit_ring();
else if(part=="pcb_reference") print_origin() pcb_reference();
else if(part=="assembly"){{
 color("SlateGray") tray();
 color("ForestGreen") translate([0,0,seat]) pcb_reference();
 color("DarkOrange") translate([0,0,join+8]) front();
}}
else assert(false,"Unknown part name");
'''
    (ROOT/'catbadge_case.scad').write_text(head+'\n'.join(modules)+'\n'+tray)
    data={
      'project':'CatBadge edge-capture case v0.1', 'status':'unprinted and not physically fit-tested',
      'source_url':SOURCE_URL,'source_access_date':'2026-09-07',
      'source_file':'2024_def_con_badge_v1.kicad_pcb','source_retrieval':'Edge.Cuts and selected footprint data read through web; complete upstream CAD assembly not imported',
      'native_coordinate_system':'KiCad XY in mm, Y down',
      'mechanical_coordinate_system':'x=KiCad_x-150, y=100-KiCad_y',
      'print_translation_xy':[-bounds[0],-bounds[1]],
      'parameters':q, 'exterior_edge_segments_native':EDGES,'selected_placements_native':PLACEMENTS,
      'dimensions_mm':{
          'pcb_outline_width':d['pcb'].bounds[2]-d['pcb'].bounds[0],
          'pcb_outline_height':d['pcb'].bounds[3]-d['pcb'].bounds[1],
          'case_width_including_lugs':bounds[2]-bounds[0],
          'case_height_including_lugs':bounds[3]-bounds[1],
          'rear_tray_height':d['join'],'front_frame_height':q['front_frame_thickness'],
          'assembled_case_depth_excluding_badge_protrusions':d['join']+q['front_frame_thickness'],
          'pcb_underside_above_print_bed':d['seat'],
          'battery_aperture_nominal':[37,62],
      },
      'lug_centers_mechanical_xy':d['lugs'],
      'geometries':{k:mapping(d[k]) for k in ['pcb','outer','floor','wall','front','ring','battery','top_access','pcb_reference']},
      'port_reliefs':{k:mapping(v) for k,v in d['ports'].items()},
      'limitations':[
         'Not physically fitted to a badge; verify PCB revision, actual battery holder, edge components and solder protrusions.',
         'Only selected footprints were reviewed; this is not a complete all-component interference check.',
         'Front screen and LEDs are exposed; frame is not guaranteed taller than screen.',
         'Battery holder protrudes through open back; no battery cover.',
         'Wide port reliefs are deliberate starting dimensions, not cable-specific measured cutouts.',
         '3MF exports are geometry only, not printer profiles or sliced G-code.',
         'No screws, nuts, washers, PCB, screen, batteries or electronics are supplied by printed parts.'
      ]
    }
    (ROOT/'design_data.json').write_text(json.dumps(data,indent=2))
    print(json.dumps(data['dimensions_mm'],indent=2))
    print('Lug coordinates',d['lugs'])
    print('Exterior vertices',len(d['pcb'].exterior.coords),'Outline valid',d['pcb'].is_valid)
    print('SCAD generated:',ROOT/'catbadge_case.scad')

if __name__=='__main__': main()
