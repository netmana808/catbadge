"""Front ear roofs with LED-aligned stripes and an open rotated SAO footprint."""
import math
import numpy as np
from shapely.geometry import Point,LineString,Polygon,box,mapping
from shapely.ops import unary_union
from shapely import affinity
import v03_reference as v
P=dict(slot_length=6.4,slot_width=3.2,inward_rake_degrees=-20.,sao_clearance=1.5,
       roof_bottom=11.2,roof_top=13.2,
       sao_pin1_xy=[37.872439,32.503094],sao_kicad_rotation=-52.,
       spring_status='unconfirmed; default lid preserves inner-left-ear access')
LEDS={'D9':[-47.5,37.5],'D11':[-52.,33.],'D12':[-55.,28.5],'D13':[-58.,24.],'D14':[-60.,19.5],
      'D7':[47.5,37.5],'D5':[52.,33.],'D8':[55.,28.5],'D6':[58.,24.],'D2':[60.,19.5]}
SLOTS={}
for ref,(x,y) in LEDS.items():
 sign=1 if x>0 else -1
 direction=np.array([-sign*math.cos(math.radians(P['inward_rake_degrees'])),math.sin(math.radians(P['inward_rake_degrees']))])
 half=(P['slot_length']-P['slot_width'])/2;centre=np.array([x,y])
 SLOTS[ref]=LineString([centre-half*direction,centre+half*direction]).buffer(P['slot_width']/2,quad_segs=24)
a=math.radians(P['sao_kicad_rotation']);cx,cy=P['sao_pin1_xy']
# KiCad uses local +Y down and its placement rotation is clockwise in native XY.
# After the project Y flip, global assembly = [cos(a), sin(a); sin(a), -cos(a)].
SAO_COURTYARD=affinity.affine_transform(box(-1.800001,-1.76,6.85,4.34),[math.cos(a),math.sin(a),math.sin(a),-math.cos(a),cx,cy])
SAO_OPEN=SAO_COURTYARD.buffer(P['sao_clearance'],quad_segs=16)
LED_OPEN=unary_union(list(SLOTS.values()))
SPRING_OPEN=v.EAR_WINDOWS.intersection(box(-45,15,-27,70))

def roof(spring_access=True):
 holes=unary_union([LED_OPEN,SAO_OPEN]+([SPRING_OPEN] if spring_access else []))
 return v.EAR_WINDOWS.difference(holes),holes

def data():
 return {**P,'leds_xy':LEDS,'slots':{k:mapping(g) for k,g in SLOTS.items()},'sao_courtyard':mapping(SAO_COURTYARD),'sao_opening':mapping(SAO_OPEN),'spring_access':mapping(SPRING_OPEN),
         'source':'work/v6/reference/badge.kicad_pcb, pinned Retia PCB; F.Cu LEDs and J5 courtyard extracted',
         'optics':'Direct-view open slots. No translucent plastic, light pipes or photometric simulation.'}
