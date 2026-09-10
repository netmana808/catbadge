#!/usr/bin/env python3
"""V8.4 compact handheld polish; all exports are unprinted prototypes."""
import json,sys
import numpy as np
from shapely.geometry import box
from generate_v83 import *
import generate_v83 as prior
import finish_v84 as finish
P={**prior.P,'version':'8.4','finishing':finish.P}
def lid_layers(spring=True,overlap=None):return finish.finish_layers(prior.lid_layers(spring,overlap),'lid')
def rear_layers():return finish.finish_layers(prior.rear_layers(),'rear')
def cover_layers():return finish.finish_layers(prior.base.cover_layers(),'cover')
def lid_mesh(spring=True,overlap=None,region=None):
 layers=lid_layers(spring,overlap)
 if region is not None:layers=[(a,c,p.intersection(region)) for a,c,p in layers]
 return finish.cut_grips(solid(layers))
def main(coupons=False):
 prints={};kit={};layouts={}
 # These full-height coupons preserve the actual side-wall stiffness geometry;
 # the shortened coupon's compliance still differs from the full perimeter.
 for overlap in P['catch_trials']:
  name='PRINT_FIRST_rim_lid_'+str(round(overlap,2)).replace('.','p')
  m=lid_mesh(overlap=overlap,region=COUPON_REGION)
  kit[name]=export(name,m,'down','tests')
 kit['PRINT_FIRST_rim_tray']=export('PRINT_FIRST_rim_tray',solid([(a,c,p.intersection(COUPON_REGION)) for a,c,p in rear_layers()]),'up','tests')
 region=box(-23,-48,36,-38)
 for name,ls in [('PRINT_FIRST_latch_cover',cover_layers()),('PRINT_FIRST_latch_tray',rear_layers())]:
  kit[name]=export(name,solid([(a,c,p.intersection(region)) for a,c,p in ls]),'up','tests')
 for name,region in [('PRINT_FIRST_front_buttons',box(-78,-18,-33,18)),('PRINT_FIRST_right_ear_SAO',box(27,15,70,46))]:
  kit[name]=export(name,lid_mesh(region=region),'down','tests')
 for dia in old.P['socket_trials']:
  name=f'cap_socket_{dia:.1f}'.replace('.','p');prints[name]=export(name,finish.cap_mesh(dia),'down');kit[name]=prints[name]
 kit['PRINT_FIRST_screen_52p5x40']=export('PRINT_FIRST_screen_52p5x40',solid([(11.2,12.8,v.screen_hole().buffer(3.,quad_segs=24).difference(v.screen_hole()))]),'down','tests')
 region=box(-77,-20,-62,-4)
 kit['PRINT_FIRST_cheek_grip']=export('PRINT_FIRST_cheek_grip',lid_mesh(region=region),'down','tests')
 region=box(14,-10,23,10)
 kit['PRINT_FIRST_cover_edge']=export('PRINT_FIRST_cover_edge',solid([(a,c,p.intersection(region)) for a,c,p in cover_layers()]),'up','tests')
 layouts['comfort']=old.write_kit('PRINT_FIRST_v8.4_Comfort_Only',{n:kit[n] for n in ['PRINT_FIRST_cheek_grip','PRINT_FIRST_cover_edge','cap_socket_3p2']})
 layouts['coupons']=old.write_kit('PRINT_FIRST_v8.4_Fit_and_Comfort',kit)
 if not coupons:
  for name,spring in [('faceplate',True),('faceplate_NO_SPRING_ONLY',False)]:prints[name]=export(name,lid_mesh(spring),'down')
  prints['rear_tray']=old.cut_port('rear_tray',solid(rear_layers()))
  prints['battery_cover']=export('battery_cover',solid(cover_layers()))
  for spring in [True,False]:
   face='faceplate' if spring else 'faceplate_NO_SPRING_ONLY';placed={}
   for name,xy in [(face,(3,3)),('rear_tray',(3,99)),('battery_cover',(158,3))]:
    m=prints[name].copy();m.apply_translation([*xy,0]);placed[name]=m
   for i,name in enumerate(v.BUTTONS):
    m=prints['cap_socket_3p2'].copy();m.apply_translation([3+14*i,199,0]);placed['button_'+name+'_TRIAL_3p2']=m
   filename='CatBadge-v8.4-COMBINED-HANDHELD'+('' if spring else '-NO-SPRING-ONLY')
   old.export_3mf(placed,ROOT/(filename+'.3mf'));layouts[filename]=list(placed)
  solid([(0,1.6,v.D['pcb_reference'])]).export(ROOT/'preview/pcb_REFERENCE_ASSEMBLY.stl')
 (ROOT/'parameters.json').write_text(json.dumps({**P,'snaps':[{k:val.tolist() if isinstance(val,np.ndarray) else val for k,val in s.items()} for s in SNAPS],'inherited_button_parameters':old.P,'ear_parameters':old.ears.data()},indent=2))
 (ROOT/'layouts.json').write_text(json.dumps(layouts,indent=2));print('BUILD COMPLETE',flush=True)
if __name__=='__main__':main('--coupons' in sys.argv)
