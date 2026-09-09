"""Measured-holder cover and shallow rear shell; PCB underside is assembly Z=0."""
import math
import numpy as np
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
import v03_reference as v

P=dict(holder_width=32.7,holder_length=59.7,holder_height=15.7,
       height_clearance=1.0,wall=1.6,rear_floor=1.6,rear_clearance=8.0,
       cavity_width=41.0,end_clearance=1.0,centre_y=-10.0,
       tab_y=[-10.0,10.0],tab_width=5.0,tab_projection=2.8,
       tab_clearance=.4,tab_step=.2,release_slide=3.2,
       screw_xy=[0.0,-46.4],screw_hole=4.4,nut_AF=7.4,nut_depth=3.4,
       screw_head_recess=7.0,post_radius=5.0,post_top=-4.2)
BACK=-P['rear_clearance']-P['rear_floor']
COVER_INNER_Z=-P['holder_height']-P['height_clearance']
COVER_OUTER_Z=COVER_INNER_Z-P['wall']
INNER_X=P['cavity_width']/2
OUTER_X=INNER_X+P['wall']
CY=P['centre_y'];HL=P['holder_length']/2+P['end_clearance']
INNER=v.round_box(-INNER_X,CY-HL,INNER_X,CY+HL,.6)
OUTER=v.round_box(-OUTER_X,CY-HL-P['wall'],OUTER_X,CY+HL+P['wall'],2.2)
POST=v.circle(*P['screw_xy'],P['post_radius'])
SCREW=v.circle(*P['screw_xy'],P['screw_hole']/2)
HEAD=v.circle(*P['screw_xy'],P['screw_head_recess']/2)
r=P['nut_AF']/math.sqrt(3);x,y=P['screw_xy']
NUT=Polygon([(x+r*math.cos(math.radians(30+60*i)),y+r*math.sin(math.radians(30+60*i))) for i in range(6)])
HOLDER=box(-P['holder_width']/2,CY-P['holder_length']/2,P['holder_width']/2,CY+P['holder_length']/2)

def tabs(z):
    if not BACK<=z<BACK+P['tab_projection']:return Polygon()
    # One 0.2 mm outward step per 0.2 mm layer: a 45-degree envelope.
    reach=min(P['tab_projection'],math.floor((z-BACK)/P['tab_step']+1)*P['tab_step'])
    return unary_union([box(-OUTER_X-reach,y-P['tab_width']/2,-INNER_X,y+P['tab_width']/2) for y in P['tab_y']])

def slots(z):
    reach=max(0,math.floor((z-BACK)/P['tab_step']+1)*P['tab_step'])
    return unary_union([box(-OUTER_X-reach-P['tab_clearance'],y-P['tab_width']/2-P['tab_clearance'],-18.0,y+P['tab_width']/2+P['tab_clearance']) for y in P['tab_y']])

def rear_layers(main_holes,main_nuts):
    d=v.D;q=v.ORIGINAL_PARAMS
    zs=[BACK,-8.0,BACK+P['nut_depth'],P['post_top']-P['nut_depth'],P['post_top'],0,1.8]
    zs += [a-d['seat'] for a,_,_ in d['ramps']]+[-q['ledge_thickness']]
    zs += list(np.arange(BACK,-8.0+.001,P['tab_step']))
    zs=sorted(set(round(z,6) for z in zs if BACK<=z<=1.8))
    result=[]
    for a,b in zip(zs,zs[1:]):
        z=(a+b)/2
        if z < -8:g=d['floor']
        elif z<d['ramp_start']-d['seat']:g=d['wall']
        elif z<-.8:
            g=next(poly for zz,h,poly in d['ramps'] if zz-d['seat']<=z<zz+h-d['seat'])
        elif z<0:g=d['ledges']
        else:g=d['wall']
        g=g.difference(main_holes)
        if z<BACK+P['nut_depth']:g=g.difference(main_nuts)
        if z < -8:g=g.difference(slots(z))
        if z<P['post_top']:
            g=unary_union([g,POST]).difference(SCREW)
            if z>P['post_top']-P['nut_depth']:g=g.difference(NUT)
        result.append((a,b,g))
    return result

def cover_layers():
    zs=[COVER_OUTER_Z,COVER_INNER_Z,BACK-P['wall'],BACK,BACK+P['tab_projection']]
    zs+=list(np.arange(BACK,BACK+P['tab_projection']+.001,P['tab_step']))
    zs=sorted(set(round(z,6) for z in zs))
    result=[]
    for a,b in zip(zs,zs[1:]):
        z=(a+b)/2
        if z<BACK:
            g=unary_union([OUTER,POST])
            if z>=COVER_INNER_Z:g=g.difference(INNER)
            g=g.difference(HEAD if z<BACK-P['wall'] else SCREW)
        else:g=Polygon()
        g=unary_union([g,tabs(z)])
        result.append((a,b,g))
    return result

def female_coupon():
    region=box(-29,-14,-18.5,-6)
    zs=np.linspace(BACK,-8,9)
    return [(a,b,region.difference(slots((a+b)/2))) for a,b in zip(zs,zs[1:])]

def male_coupon():
    region=box(-29,-13,-19,-7)
    return [(a,b,g.intersection(region)) for a,b,g in cover_layers()]

def nut_coupon():
    return [(BACK,P['post_top']-P['nut_depth'],POST.difference(SCREW)),
            (P['post_top']-P['nut_depth'],P['post_top'],POST.difference(NUT))]
