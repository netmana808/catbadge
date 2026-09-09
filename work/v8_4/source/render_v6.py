"""Render actual exported CAD meshes, not an AI-generated depiction."""
from pathlib import Path
import json,math,sys
# Import only the rendering modules; importing all VTK modules stalls in
# macOS dynamic-library loading on this host (see work/render-sample.txt).
from types import SimpleNamespace
from vtkmodules.vtkCommonDataModel import vtkPlane
from vtkmodules.vtkFiltersCore import vtkClipPolyData, vtkPolyDataNormals
from vtkmodules.vtkFiltersSources import vtkCubeSource
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkIOImage import vtkPNGWriter
from vtkmodules.vtkRenderingCore import (vtkActor, vtkPolyDataMapper, vtkRenderer,
    vtkRenderWindow, vtkWindowToImageFilter)
import vtkmodules.vtkRenderingOpenGL2
vtk=SimpleNamespace(**{key:value for key,value in list(globals().items()) if key.startswith('vtk') and key!='vtkmodules'})
from PIL import Image,ImageDraw,ImageFont
import generate_v6 as g
ROOT=g.ROOT
BG=(.047,.071,.106)
BLUE=(.43,.61,.69); ORANGE=(.98,.55,.25)

def actor(ren,m,col,offset=(0,0,0),clip=False):
 reader=vtk.vtkSTLReader();reader.SetFileName(str(m));reader.Update()
 src=reader.GetOutputPort()
 if clip:
  plane=vtk.vtkPlane();plane.SetOrigin(0,0,0);plane.SetNormal(0,1,0)
  cl=vtk.vtkClipPolyData();cl.SetInputConnection(src);cl.SetClipFunction(plane);cl.Update();src=cl.GetOutputPort()
 normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(src);normals.SetFeatureAngle(40);normals.SplittingOn();normals.ConsistencyOn();normals.Update()
 mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
 a=vtk.vtkActor();a.SetMapper(mapper);a.SetPosition(*offset)
 p=a.GetProperty();p.SetColor(*col);p.SetAmbient(.35);p.SetDiffuse(.65);p.SetSpecular(.15);p.SetSpecularPower(22)
 ren.AddActor(a);return a

def cube(ren,bounds,col):
 s=vtk.vtkCubeSource();s.SetBounds(*bounds)
 m=vtk.vtkPolyDataMapper();m.SetInputConnection(s.GetOutputPort());a=vtk.vtkActor();a.SetMapper(m);a.GetProperty().SetColor(*col);a.GetProperty().SetAmbient(.5);ren.AddActor(a)

def render(name,mode):
 ren=vtk.vtkRenderer();ren.SetBackground(*BG)
 rw=vtk.vtkRenderWindow();rw.AddRenderer(ren);rw.SetOffScreenRendering(1);rw.SetSize(1700,1040);rw.SetMultiSamples(8)
 base=ROOT/'preview'
 if mode in ['assembly','antenna']:
  actor(ren,base/'rear_tray_M4_ASSEMBLY.stl',(.22,.30,.35))
  actor(ren,base/'pcb_REFERENCE_ASSEMBLY.stl',(.09,.35,.26))
  sx,sy=g.v.SCREEN_REFERENCE_CENTER
  cube(ren,(sx-24.48,sx+24.48,sy-18.36,sy+18.36,10.2,10.5),(.07,.16,.24))
  actor(ren,base/'faceplate_SIDE6p5_TEARDROP_TRIAL_ASSEMBLY.stl',BLUE)
  for xy in g.v.BUTTONS.values():actor(ren,base/'cap_TALL_socket_3p2_ASSEMBLY.stl',ORANGE,(*xy,0))
  cam=ren.GetActiveCamera();cam.ParallelProjectionOn();cam.SetViewUp(0,1,0)
  if mode=='assembly':
   cam.SetPosition(100,165,285);cam.SetFocalPoint(0,-3,1);cam.SetParallelScale(64)
  else:
   x,y=g.C
   cam.SetPosition(x+g.N[0]*80,y+g.N[1]*80,40);cam.SetFocalPoint(x,y,6.7);cam.SetViewUp(0,0,1);cam.SetParallelScale(17)
 elif mode=='retention':
  actor(ren,base/'faceplate_SIDE6p5_TEARDROP_TRIAL_ASSEMBLY.stl',BLUE)
  cam=ren.GetActiveCamera();cam.ParallelProjectionOn();cam.SetViewUp(0,0,1)
  cam.SetPosition(12,-115,-50);cam.SetFocalPoint(0,-37,5);cam.SetParallelScale(40)
 else:
  actor(ren,base/'cap_SHORT_socket_3p2_ASSEMBLY.stl',ORANGE,(-9,0,0))
  actor(ren,base/'cap_TALL_socket_3p2_ASSEMBLY.stl',ORANGE,(9,0,0))
  cam=ren.GetActiveCamera();cam.SetPosition(23,-42,-45);cam.SetFocalPoint(0,0,8);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(18)
 ren.ResetCameraClippingRange();rw.Render()
 im=vtk.vtkWindowToImageFilter();im.SetInput(rw);im.SetInputBufferTypeToRGB();im.ReadFrontBufferOff();im.Update()
 wr=vtk.vtkPNGWriter();wr.SetFileName(str(base/name));wr.SetInputConnection(im.GetOutputPort());wr.Write();rw.Finalize()

def font(n,b=False):
 candidates=[
  '/usr/share/fonts/truetype/dejavu/'+('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'),
  '/System/Library/Fonts/Supplemental/'+('Arial Bold.ttf' if b else 'Arial.ttf'),
  'C:/Windows/Fonts/'+('arialbd.ttf' if b else 'arial.ttf'),
 ]
 for path in candidates:
  if Path(path).is_file():return ImageFont.truetype(path,n)
 return ImageFont.load_default(size=n)
def frame(raw,out,title,sub,foot1,foot2):
 im=Image.new('RGB',(1700,1270),tuple(round(v*255) for v in BG));im.paste(Image.open(ROOT/'preview'/raw),(0,113));dr=ImageDraw.Draw(im)
 dr.text((50,25),title,font=font(35,True),fill='#EAF2F5')
 dr.text((50,78),sub,font=font(20),fill='#A8BCC8')
 dr.text((1650,34),'v6 / UNPRINTED',font=font(20,True),fill='#FFB579',anchor='ra')
 dr.text((50,1160),foot1,font=font(22,True),fill='#EAF2F5')
 dr.text((50,1207),foot2,font=font(20),fill='#A8BCC8')
 im.save(ROOT/'preview'/out)

def main():
 for exploded in [False,True]:
  ren=vtk.vtkRenderer();ren.SetBackground(*BG)
  rw=vtk.vtkRenderWindow();rw.AddRenderer(ren);rw.SetOffScreenRendering(1);rw.SetSize(1700,1040)
  base=ROOT/'preview'
  actor(ren,base/'faceplate_SIDE6p5_TEARDROP_TRIAL_ASSEMBLY.stl',BLUE)
  actor(ren,base/'rear_tray_M4_ASSEMBLY.stl',(.25,.36,.40))
  actor(ren,base/'battery_cover_ASSEMBLY.stl',ORANGE,(3.2,0,-28) if exploded else (0,0,0))
  if exploded:
   b=g.battery
   cube(ren,(-16.35,16.35,-39.85,19.85,-15.7,0),(.35,.55,.35))
  cam=ren.GetActiveCamera();cam.ParallelProjectionOn();cam.SetPosition(-85,-130,-240);cam.SetFocalPoint(0,-3,-8);cam.SetViewUp(0,1,0);cam.SetParallelScale(68)
  ren.ResetCameraClippingRange();rw.Render()
  im=vtk.vtkWindowToImageFilter();im.SetInput(rw);im.SetInputBufferTypeToRGB();im.ReadFrontBufferOff();im.Update()
  stem='battery_exploded' if exploded else 'battery_assembled'
  wr=vtk.vtkPNGWriter();wr.SetFileName(str(base/(stem+'_raw.png')));wr.SetInputConnection(im.GetOutputPort());wr.Write();rw.Finalize()
  frame(stem+'_raw.png',stem+'.png','V6 / SLIM REAR + REMOVABLE AA COVER',
   'Actual exported parts. Green box in exploded view represents the measured holder envelope only.',
   '22.8 mm main body / 31.5 mm over battery cover / Two tapered tabs + independent M4 screw',
   'Undo cover screw, slide 3.2 mm toward assembly +X, then lift away. Physical fit remains untested.')
 render('raw_retention.png','retention')
 frame('raw_retention.png','lower_retention_detail.png','LOWER EDGE / COMPLETE SCREW TUBE',
  'Actual exported lid, seen from below toward the lower edge. PCB omitted for visibility.',
  'Complete lower screw-tube wall / M4 bore and head recess retained / Open slots and PCB ribs',
  'The tube now grows continuously from the print bed; physical fit and print quality remain untested.')
 render('raw_faceplate.png','assembly')
 frame('raw_faceplate.png','faceplate_v6_preview.png','CATBADGE / SIDE MOUNT + SLIP-ON CAPS',
  'Actual exported CAD geometry. Screen and PCB are simplified references; connector not modelled.',
  '10 mm button faces / 61 x 40 mm screen opening / M4 holes and nut pockets / Original seat retained',
  'No antenna loop. Trial hole exits the upper-left ear wall, parallel to the PCB.')
 render('raw_antenna.png','antenna')
 frame('raw_antenna.png','side_mount_detail.png','ANTENNA / INTEGRATED WALL MOUNT',
  'Actual side-hole mesh, viewed toward the upper-left ear. No antenna connector fitted.',
  '6.5 mm TRIAL clearance / pointed roof / 2.4 mm panel / Flat inner and outer seats',
  'Confirm the threaded shank, nut/washer size and internal cable clearance before using the full lid.')
 render('raw_caps.png','caps')
 frame('raw_caps.png','slip_on_caps_detail.png','BUTTONS / SOCKETS ON THE UNDERSIDE',
  'Left: low-profile cap for the open badge. Right: taller cap for the new v6 faceplate.',
  'Flat 10 mm faces / 4.8 mm stem / 1.5 mm socket depth / Bores: 3.0, 3.1, 3.2, 3.3 mm',
  'Shown from below. Stem-mounted, not flange-captive. Trial fit must not require force on the switch.')
 print('Rendered battery cover, assembly and front-detail previews from actual meshes')

if __name__=="__main__":main()
