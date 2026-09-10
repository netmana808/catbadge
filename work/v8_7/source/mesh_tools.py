#!/usr/bin/env python3
"""Export watertight STL/3MF directly from layered CAD cross-sections.

Avoids slow OpenSCAD 3-D boolean unions. Requires numpy, shapely>=2.1, trimesh.
All layer boundaries are globally noded before triangulation, so stacked
surfaces share exactly the same vertices. Fails if a result is not watertight,
outward oriented and a single connected positive-volume solid.
Run after build_case.py: python export_meshes.py
"""
from __future__ import annotations
import json, math, sys, time, zipfile, hashlib
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
import numpy as np
import shapely
from shapely import constrained_delaunay_triangles, set_precision
from shapely.geometry import Polygon, Point, LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely.strtree import STRtree
import trimesh
from build_case import PARAMS, make_design, ROOT, circle
GRID=0.00001

def clean(g):
    g=set_precision(g,GRID)
    if not g.is_valid: raise ValueError('Invalid cross-section')
    return g

def polygons(g):
    if g.is_empty: return []
    if g.geom_type=='Polygon': return [g]
    if g.geom_type=='MultiPolygon': return list(g.geoms)
    if g.geom_type=='GeometryCollection':
        out=[]
        for x in g.geoms: out.extend(polygons(x))
        return out
    return []

def rings(g):
    for poly in polygons(g):
        poly=orient(poly,sign=1)
        yield poly.exterior
        yield from poly.interiors

def vertices_of_lines(g):
    if hasattr(g,'geoms'):
        for v in g.geoms: yield from vertices_of_lines(v)
    elif hasattr(g,'coords'):
        yield from g.coords

def layered_mesh(layers: list[tuple[float,float,object]]) -> trimesh.Trimesh:
    layers=[(round(a,6),round(b,6),clean(g)) for a,b,g in layers if b-a>1e-7]
    assert all(abs(layers[i][1]-layers[i+1][0])<1e-7 for i in range(len(layers)-1))
    for _,_,g in layers:
        if not polygons(g): raise ValueError('Missing layer polygon')
    # Build all horizontal exposed regions first, so their exact overlay nodes
    # participate in the shared line network too.
    caps=[(layers[0][0],layers[0][2],-1),(layers[-1][1],layers[-1][2],1)]
    for (_,z,below),(_,_,above) in zip(layers,layers[1:]):
        caps.append((z,clean(below.difference(above)),1))
        caps.append((z,clean(above.difference(below)),-1))
    network=unary_union([g.boundary for _,_,g in layers]+[g.boundary for _,g,_ in caps if not g.is_empty])
    nodes=sorted({(round(x,5),round(y,5)) for x,y in vertices_of_lines(network)})
    nodearray=np.asarray(nodes,dtype=float)
    tree=STRtree([Point(v) for v in nodes])
    cache={}
    def densify_ring(r):
        coords=list(r.coords);out=[]
        for a,b in zip(coords,coords[1:]):
            a=np.array(a);b=np.array(b);delta=b-a;length2=float(np.dot(delta,delta))
            if length2<1e-14: continue
            key=(tuple(a),tuple(b))
            if key not in cache:
                ids=tree.query(LineString([a,b]).buffer(GRID*0.15,cap_style=3))
                candidates=nodearray[ids]
                t=(candidates-a)@delta/length2
                projected=a+t[:,None]*delta
                err=np.linalg.norm(projected-candidates,axis=1)
                valid=(t>=-1e-8)&(t<1-1e-8)&(err<GRID*0.2)
                chosen=candidates[valid][np.argsort(t[valid])]
                if len(chosen)==0 or np.linalg.norm(chosen[0]-a)>GRID:
                    chosen=np.vstack([a,chosen])
                cache[key]=[tuple(c) for c in chosen]
            out.extend(cache[key])
        return out
    verts=[];faces=[];index={}
    def vi(x,y,z):
        key=(round(float(x),5),round(float(y),5),round(float(z),6))
        if key not in index: index[key]=len(verts);verts.append(key)
        return index[key]
    def face(points):
        ids=[vi(*p) for p in points]
        if len(set(ids))==3: faces.append(ids)
    for z0,z1,g in layers:
        for ring in rings(g):
            xy=densify_ring(ring)
            for a,b in zip(xy,xy[1:]+xy[:1]):
                face([(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1)])
                face([(a[0],a[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)])
    for z,g,normal in caps:
        for p in polygons(g):
            p=orient(p,sign=1)
            outer=densify_ring(p.exterior)
            holes=[densify_ring(r) for r in p.interiors]
            dense=Polygon(outer,holes)
            if not dense.is_valid: raise ValueError('Noding produced invalid cap')
            ts=constrained_delaunay_triangles(dense)
            for t in ts.geoms:
                xy=list(t.exterior.coords)[:3]
                a,b,c=np.array(xy)
                sign=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                if sign*normal<0: xy=xy[::-1]
                face([(x,y,z) for x,y in xy])
    m=trimesh.Trimesh(vertices=np.array(verts),faces=np.array(faces),process=False)
    m.remove_unreferenced_vertices()
    # Overlay-grid rounding can leave an interface point a few micrometres off
    # a shared long edge. Split those boundary triangles at the existing vertex;
    # never cap arbitrary holes or move the case surfaces.
    for repair in range(200):
        if m.is_watertight: break
        counts=np.bincount(m.edges_unique_inverse)
        bad_ids=np.flatnonzero(counts==1)
        if np.any(counts>2): raise ValueError('Overlapping/non-manifold mesh faces')
        bad=m.edges_unique[bad_ids]
        bverts=np.unique(bad)
        found=False
        for eid,(a,b) in zip(bad_ids,bad):
            pa=m.vertices[a];pb=m.vertices[b];delta=pb-pa;ll=float(np.dot(delta,delta))
            if ll<1e-12: continue
            cs=bverts[(bverts!=a)&(bverts!=b)]
            ts=(m.vertices[cs]-pa)@delta/ll
            dist=np.linalg.norm(m.vertices[cs]-(pa+ts[:,None]*delta),axis=1)
            valid=np.flatnonzero((ts>1e-7)&(ts<1-1e-7)&(dist<GRID*4))
            if len(valid)==0: continue
            k=valid[np.argmin(dist[valid])];c=int(cs[k])
            fi=int(np.flatnonzero(m.edges_unique_inverse==eid)[0]//3)
            f=m.faces[fi].tolist()
            for j in range(3):
                u,v,w=f[j],f[(j+1)%3],f[(j+2)%3]
                if {u,v}=={int(a),int(b)}: break
            fs=np.delete(m.faces,fi,axis=0)
            fs=np.vstack([fs,[u,c,w],[c,v,w]])
            m=trimesh.Trimesh(vertices=m.vertices,faces=fs,process=False)
            found=True
            break
        if not found: break
    if not m.is_watertight:
        m.export(ROOT.parent/'preview'/'debug_failed_mesh.ply')
        counts=np.bincount(m.edges_unique_inverse)
        bad=m.edges_unique[counts!=2]
        raise ValueError(f'Mesh is not watertight: {len(bad)} non-manifold edges; samples {m.vertices[bad[:5]].tolist()}')
    expected_volume=sum((z1-z0)*g.area for z0,z1,g in layers)
    if abs(m.volume-expected_volume)>max(0.003,expected_volume*1e-6): raise ValueError(f'Volume mismatch {m.volume} vs {expected_volume}')
    if not m.is_winding_consistent or m.volume<=0: raise ValueError('Mesh winding or volume failure')
    if len(m.split(only_watertight=False))!=1: raise ValueError('Mesh contains disconnected solids')
    return m

NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
def export_3mf(meshes:dict[str,trimesh.Trimesh],path:Path) -> None:
    model=ET.Element(f'{{{NS}}}model',{'unit':'millimeter','xml:lang':'en-US'})
    ET.SubElement(model,f'{{{NS}}}metadata',{'name':'Title'}).text='CatBadge v8.7 — closed rear shell and reinforced rim; unprinted PLA+ prototype'
    ET.SubElement(model,f'{{{NS}}}metadata',{'name':'Description'}).text='Geometry only. No printer profile, supports, or G-code. Read README before printing.'
    resources=ET.SubElement(model,f'{{{NS}}}resources');build=ET.SubElement(model,f'{{{NS}}}build')
    for i,(name,m) in enumerate(meshes.items(),1):
        obj=ET.SubElement(resources,f'{{{NS}}}object',{'id':str(i),'type':'model','name':name})
        mesh=ET.SubElement(obj,f'{{{NS}}}mesh')
        vs=ET.SubElement(mesh,f'{{{NS}}}vertices');ts=ET.SubElement(mesh,f'{{{NS}}}triangles')
        for v in m.vertices: ET.SubElement(vs,f'{{{NS}}}vertex',{a:f'{float(val):.6f}' for a,val in zip('xyz',v)})
        for f in m.faces: ET.SubElement(ts,f'{{{NS}}}triangle',{f'v{j+1}':str(int(v)) for j,v in enumerate(f)})
        ET.SubElement(build,f'{{{NS}}}item',{'objectid':str(i)})
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>''')
        z.writestr('_rels/.rels','''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>''')
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))

def main():
    t=time.time(); d=make_design();q=PARAMS;out=ROOT.parent
    holes=unary_union([circle(x,y,q['screw_clearance_diameter']/2) for x,y in d['lugs']])
    nuts=[]
    radius=q['nut_across_flats']/math.sqrt(3)
    for x,y in d['lugs']:
        nuts.append(Polygon([(x+radius*math.cos(math.radians(30+60*i)),y+radius*math.sin(math.radians(30+60*i))) for i in range(6)]))
    nuts=unary_union(nuts)
    layers=[(0,q['floor'],d['floor'].difference(nuts).difference(holes)),
            (q['floor'],q['nut_recess_depth'],d['wall'].difference(nuts).difference(holes)),
            (q['nut_recess_depth'],d['ramp_start'],d['wall'].difference(holes))]
    layers.extend((z,z+h,g.difference(holes)) for z,h,g in d['ramps'])
    layers.append((d['seat']-q['ledge_thickness'],d['seat'],d['ledges'].difference(holes)))
    layers.append((d['seat'],d['join'],d['wall'].difference(holes)))
    jobs={
      'catbadge_fit_ring':[(0,q['fit_ring_height'],d['ring'])],
      'catbadge_front_frame':[(0,q['front_frame_thickness'],d['front'].difference(holes))],
      'catbadge_rear_tray':layers,
      'pcb_reference_DO_NOT_PRINT':[(0,q['pcb_thickness'],d['pcb_reference'])],
    }
    checks={};meshes={}
    translation=[-d['outer'].bounds[0],-d['outer'].bounds[1],0]
    for name,ls in jobs.items():
        print('Generating',name,flush=True)
        m=layered_mesh(ls);m.apply_translation(translation)
        if name.startswith('pcb_'):
            m.export(out/'preview'/f'{name}.stl');continue
        meshes[name]=m
        path=out/f'{name}.stl';m.export(path)
        export_3mf({name:m},out/f'{name}.3mf')
        # Verify actual STL bytes, not just the in-memory model.
        loaded=trimesh.load_mesh(path,process=True)
        assert loaded.is_watertight and loaded.is_winding_consistent and loaded.volume>0
        assert len(loaded.split())==1
        loaded3=trimesh.load(out/f'{name}.3mf',force='mesh')
        assert loaded3.is_watertight and np.allclose(loaded3.bounds,loaded.bounds,atol=0.0001)
        checks[name]={'watertight':bool(loaded.is_watertight),'consistent_winding':bool(loaded.is_winding_consistent),
          'connected_solids':len(loaded.split()),'triangles':len(loaded.faces),'bounds_mm':loaded.bounds.tolist(),
          'dimensions_mm':loaded.extents.tolist(),'solid_volume_cm3':float(loaded.volume/1000),
          'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'stl_roundtrip':'passed','3mf_roundtrip':'passed'}
        print(name,checks[name],flush=True)
    # Both case parts on a generic ~160 x 196 mm layout; fit ring stays separate.
    tray=meshes['catbadge_rear_tray'].copy();frame=meshes['catbadge_front_frame'].copy()
    frame.apply_translation([0,float(tray.extents[1])+6,0])
    export_3mf({'Rear tray':tray,'Front frame':frame},out/'catbadge_case_parts.3mf')
    report={'status':'digital mesh validation only; not physically printed or fitted',
            'checks':checks,'elapsed_seconds':round(time.time()-t,2),
            'method':'2.5D section surface meshing with global boundary noding and constrained Delaunay cap triangulation'}
    (out/'validation_report.json').write_text(json.dumps(report,indent=2))
    print('Done:',report['elapsed_seconds'],'seconds',flush=True)

if __name__=='__main__': main()
