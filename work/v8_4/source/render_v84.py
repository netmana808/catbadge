"""Actual mesh previews of V8.4. PCB outline is a simplified reference."""
from PIL import Image,ImageDraw
import generate_v84 as g
import render_v6 as r
ROOT=g.ROOT;vtk=r.vtk

def run(mode):
 ren=vtk.vtkRenderer();ren.SetBackground(*r.BG)
 rw=vtk.vtkRenderWindow();rw.AddRenderer(ren);rw.SetOffScreenRendering(1);rw.SetSize(1600,1050);rw.SetMultiSamples(8)
 base=ROOT/'preview'
 def part(name,color,offset=(0,0,0)):return r.actor(ren,base/(name+'_ASSEMBLY.stl'),color,offset)
 cam=ren.GetActiveCamera();cam.ParallelProjectionOn();cam.SetViewUp(0,1,0)
 if mode in ['front','closed_ears']:
  part('rear_tray',(.23,.32,.37));part('faceplate' if mode=='front' else 'faceplate_NO_SPRING_ONLY',r.BLUE);part('pcb_REFERENCE',(.08,.24,.18))
  for xy in g.v.BUTTONS.values():part('cap_socket_3p2',r.ORANGE,(*xy,0))
  cam.SetPosition(95,150,280);cam.SetFocalPoint(0,-3,0);cam.SetParallelScale(63)
  title='V8.4 / COMPACT HANDHELD POLISH'
  sub='Default: spring access retained.' if mode=='front' else 'Closed-ear variant: original spring antenna must be absent.'
  footer='Softened exterior edges / Beveled button faces / Subtle cheek grip lines / Original snap interfaces'
 elif mode in ['grip_detail','button_detail','cover_detail']:
  if mode=='grip_detail':
   part('PRINT_FIRST_cheek_grip',r.BLUE)
   gr=g.finish.GRIPS[2];c=gr['c']+2.8*gr['n'];n=gr['n'];t=gr['t']
   cam.SetPosition(c[0]+75*n[0]+12*t[0],c[1]+75*n[1]+12*t[1],34)
   cam.SetFocalPoint(c[0],-11.5,7);cam.SetViewUp(0,0,1);cam.SetParallelScale(10)
   title='V8.4 / FOUR GRIP LINES PER CHEEK';sub='Actual exported cheek coupon, enlarged.'
   footer='0.25 mm nominal recess / 0.8 mm width / 2.4 mm length / Mirrored 20-degree angle'
  elif mode=='button_detail':
   part('cap_socket_3p2',r.ORANGE)
   cam.SetPosition(18,-28,45);cam.SetFocalPoint(0,0,10);cam.SetViewUp(0,0,1);cam.SetParallelScale(7.5)
   title='V8.4 / SOFTER BUTTON FACE';sub='Actual exported button, enlarged; flat round top retained.'
   footer='0.3 mm face bevel / Original socket, stem and captive flange'
  else:
   part('PRINT_FIRST_cover_edge',r.ORANGE)
   cam.SetPosition(58,-33,-57);cam.SetFocalPoint(20,0,-14);cam.SetViewUp(0,0,-1);cam.SetParallelScale(12)
   title='V8.4 / BATTERY-COVER EXTERIOR EDGE';sub='Actual exported edge coupon, enlarged; exterior faces the camera.'
   footer='0.6 mm exterior bevel / Existing cover cavity and sliding interfaces'
 elif mode=='rear':
  part('faceplate',r.BLUE);part('rear_tray',(.23,.32,.37));part('battery_cover',r.ORANGE,(3.2,0,-24))
  cam.SetPosition(-80,-120,-260);cam.SetFocalPoint(0,-5,-8);cam.SetParallelScale(67)
  title='V8.4 / SLIDE + CLICK BATTERY ACCESS'
  sub='Exploded view: cover shown slid and lifted away. The main case stays closed.'
  footer='Press the bottom-edge latch toward the badge center, slide assembly +X, then lift away'
 elif mode=='rim_inside':
  part('faceplate',r.BLUE)
  cam.SetPosition(-80,-110,-180);cam.SetFocalPoint(0,-4,2);cam.SetViewUp(0,1,0);cam.SetParallelScale(63)
  title='V8.4 / FACEPLATE INNER RIM AND FOUR CATCHES'
  sub='Actual exported mesh, viewed from the rear. Rear tray omitted to expose the rim.'
  footer='Short release notches beside each catch / Existing button flanges and PCB retaining ribs'
 elif mode=='latch':
  part('PRINT_FIRST_latch_cover',r.ORANGE);part('PRINT_FIRST_latch_tray',r.BLUE,(0,0,4))
  cam.SetPosition(30,-120,35);cam.SetFocalPoint(5,-43,-10);cam.SetViewUp(0,0,1);cam.SetParallelScale(24)
  title='V8.4 / GUARDED BATTERY-COVER LATCH'
  sub='Actual bottom-strip coupons. Tray raised 4 mm to show the mating strike and latch.'
  footer='Long beam flexes toward the badge center / Existing cover tabs carry pull-off load / No cover screw'
 else:
  part('rear_tray',r.BLUE);part('faceplate',(.23,.32,.37))
  ant=g.old.antenna;c=ant.C;normal=ant.N;t=ant.T;camera=c+normal*75+t*20
  cam.SetPosition(camera[0],camera[1],15);cam.SetFocalPoint(c[0],c[1],-4);cam.SetViewUp(0,0,1);cam.SetParallelScale(16)
  title='V8.4 / OUTER-EAR REAR ANTENNA PORT'
  sub='6.5 mm trial opening and 2.4 mm land; adapter retained by its real metal nut.'
  footer='Original spring status unconfirmed / Actual adapter and cable fit remain untested'
 ren.ResetCameraClippingRange();rw.Render()
 im=vtk.vtkWindowToImageFilter();im.SetInput(rw);im.SetInputBufferTypeToRGB();im.ReadFrontBufferOff();im.Update()
 out=base/(mode+'_raw.png');wr=vtk.vtkPNGWriter();wr.SetFileName(str(out));wr.SetInputConnection(im.GetOutputPort());wr.Write();rw.Finalize()
 canvas=Image.new('RGB',(1600,1220),tuple(round(x*255) for x in r.BG));canvas.paste(Image.open(out),(0,110));d=ImageDraw.Draw(canvas)
 d.text((35,20),title,font=r.font(32,True),fill='#EAF2F5');d.text((35,69),sub,font=r.font(19),fill='#AAC2CD')
 d.text((35,1178),footer,font=r.font(19),fill='#FFD0A8');canvas.save(base/(mode+'.png'))
if __name__=='__main__':
 for mode in ['front','closed_ears','rear','rim_inside','latch','antenna','grip_detail','button_detail','cover_detail']:run(mode)
 from render_joint_section import main as section
 section()
 sheet=Image.new('RGB',(1600,1400),'#0C121B');d=ImageDraw.Draw(sheet)
 d.text((35,20),'V8.4 / HANDHELD FINISHING SAMPLES',font=r.font(32,True),fill='#EAF2F5')
 for i,name in enumerate(['grip_detail','button_detail','cover_detail']):
  tile=Image.open(ROOT/'preview'/(name+'.png')).resize((800,610))
  sheet.paste(tile,[(0,110),(800,110),(400,750)][i])
 sheet.save(ROOT/'preview/comfort.png')
 print('Rendered actual V8.4 mesh previews')
