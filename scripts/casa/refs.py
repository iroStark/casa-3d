"""Pranchas do PDF como planos de referência alinhados aos eixos (coleção 00_Referencias_PDF).

A folha 02 é posicionada pela ancoragem medida: eixo 1 -> x_px 537,67 ; eixo A -> y_px 244,33 ;
33,333 px/m na horizontal e 34,37 px/m na vertical (a prancha raster tem escala vertical
~3% diferente da horizontal — registrado em data/projeto.json).
Invisíveis no render; servem para conferência no viewport.
"""
import os
import bpy
from .core import ROOT, coll, mesh_obj

PAGES = os.path.join(ROOT, "source", "pdf_native")

def plane_from_image(name, path, x0, x1, y0, y1, z, C):
    img = bpy.data.images.load(path)
    m = bpy.data.materials.new("REF_" + name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 1
    ob = mesh_obj("REF_" + name, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [(0, 1, 2, 3)], m, C)
    uv = ob.data.uv_layers.new(name="UVMap")
    for i, co in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[i].uv = co
    ob.hide_render = True
    ob["keep_uv"] = 1
    ob["categoria"] = "referencia"
    return ob

def build():
    C = coll("00_Referencias_PDF")
    p = os.path.join(PAGES, "p-001.png")
    if os.path.exists(p):
        W, H = 1491, 1055
        sx, sy = 33.333, 34.37
        x0 = -537.67 / sx; x1 = (W - 537.67) / sx
        y1 = 244.33 / sy; y0 = -(H - 244.33) / sy
        plane_from_image("Folha02_Planta_Cotas", p, x0, x1, y0, y1, -0.30, C)
    C.hide_render = True
