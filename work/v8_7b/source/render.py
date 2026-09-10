"""Render actual faceplate and cap STL meshes, old versus new."""
from pathlib import Path
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkRenderer, vtkRenderWindow, vtkWindowToImageFilter
from vtkmodules.vtkIOImage import vtkPNGWriter
import vtkmodules.vtkRenderingOpenGL2
from PIL import Image, ImageDraw, ImageFont
from build import ROOT, BUTTONS, name


def actor(renderer, path, color, xy=(0,0)):
    reader = vtkSTLReader(); reader.SetFileName(str(path)); reader.Update()
    normals = vtkPolyDataNormals(); normals.SetInputConnection(reader.GetOutputPort())
    normals.SetFeatureAngle(45); normals.ConsistencyOn(); normals.Update()
    mapper = vtkPolyDataMapper(); mapper.SetInputConnection(normals.GetOutputPort())
    a = vtkActor(); a.SetMapper(mapper); a.SetPosition(*xy,0)
    a.GetProperty().SetColor(*color); a.GetProperty().SetAmbient(.3)
    a.GetProperty().SetDiffuse(.7); renderer.AddActor(a)


def main():
    window = vtkRenderWindow(); window.SetSize(1600,680); window.SetOffScreenRendering(1)
    for i in range(2):
        renderer = vtkRenderer(); renderer.SetViewport(i*.5,0,(i+1)*.5,1)
        renderer.SetBackground(.07,.11,.15); window.AddRenderer(renderer)
        actor(renderer, ROOT/'reference/faceplate_ASSEMBLY.stl', (.47,.67,.74))
        cap = ROOT/'reference/cap_socket_3p2_ASSEMBLY.stl' if i == 0 else ROOT/'preview'/(name(10.2,3.2)+'_ASSEMBLY.stl')
        for xy in BUTTONS.values():
            actor(renderer,cap,(1.,.63,.29),xy)
        camera = renderer.GetActiveCamera(); camera.ParallelProjectionOn()
        camera.SetPosition(-95,-125,135); camera.SetFocalPoint(0,0,6)
        camera.SetViewUp(0,0,1); camera.SetParallelScale(66)
        renderer.ResetCameraClippingRange()
    window.Render()
    capture = vtkWindowToImageFilter(); capture.SetInput(window); capture.SetInputBufferTypeToRGB()
    capture.ReadFrontBufferOff(); capture.Update()
    writer = vtkPNGWriter(); writer.SetFileName(str(ROOT/'preview/comparison-raw.png'))
    writer.SetInputConnection(capture.GetOutputPort()); writer.Write(); window.Finalize()
    fontpath = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    font = lambda size: ImageFont.truetype(str(fontpath),size) if fontpath.exists() else ImageFont.load_default(size=size)
    image = Image.new('RGB',(1600,850),'#121c26'); image.paste(Image.open(ROOT/'preview/comparison-raw.png'),(0,100))
    draw = ImageDraw.Draw(image)
    draw.text((30,20),'Existing v8.7 buttons',fill='white',font=font(30))
    draw.text((830,20),'v8.7b replacement buttons',fill='white',font=font(30))
    draw.text((30,65),'0.5 mm protrusion / 10.0 mm guide',fill='#b4c8d1',font=font(23))
    draw.text((830,65),'1.5 mm protrusion / 10.2 mm guide trial',fill='#ffb46b',font=font(23))
    draw.text((30,790),'Same faceplate, socket contact height and retaining flange. Actual STL render; physical fit untested.',fill='white',font=font(24))
    image.save(ROOT/'preview/button-comparison.png')
    # Persistent visual map for the six named, separate objects in the trial plate.
    from build import VARIANTS
    image = Image.new('RGB',(1050,740),'#121c26'); draw=ImageDraw.Draw(image)
    draw.text((35,20),'v8.7b fit-trial plate | view from above',fill='white',font=font(28))
    for i,(guide,socket) in enumerate(VARIANTS):
        x,y=185+330*(i%3),500-300*(i//3)
        draw.ellipse((x-60,y-60,x+60,y+60),fill='#ffb46b')
        draw.ellipse((x-18,y-18,x+18,y+18),fill='#121c26')
        draw.text((x-120,y+82),f'Guide {guide:.1f} / socket {socket:.1f}',fill='white',font=font(22))
    draw.text((35,682),'Layout key only. The actual 3MF names identify each variant. Keep track after removal.',fill='#b4c8d1',font=font(20))
    image.save(ROOT/'preview/fit-trial-layout.png')
    print('Rendered exported assembly meshes and trial layout key')


if __name__ == '__main__':
    main()
