"""Renderiza câmeras do modelo (mesmo .blend para todas as imagens).

blender -b blender/casa.blend -P scripts/render_stills.py -- --cams E01,I01 --scale 25 --samples 64 --out renders/teste
--cams all  -> todas as câmeras de casa/cameras.py
Modos: dia | tarde | aereo | aereo_tarde | topo | planta | planta_persp | tarde_int
"""
import sys, os, time, math
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d=None):
    return argv[argv.index(n) + 1] if n in argv else d

import casa.cameras as cams
import casa.lighting as lighting
import casa.render_setup as rs

sc = bpy.context.scene
CAMS = {c["id"]: c for c in cams.CAMS}
sel = arg("--cams", "all")
ids = list(CAMS) if sel == "all" else sel.split(",")
scale = int(arg("--scale", "100"))
samples = int(arg("--samples", "256"))
out = arg("--out", os.path.join(ROOT, "renders"))
ext = arg("--ext", "png")
os.makedirs(out, exist_ok=True)
rs.setup(sc, samples=samples)
print("VIEW", sc.view_settings.view_transform, sc.view_settings.look)
sc.render.resolution_percentage = scale
if ext == "jpg":
    sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 92

def objs_in(cname):
    c = bpy.data.collections.get(cname)
    return list(c.all_objects) if c else []

INT_LIGHTS = objs_in("12b_Luzes_Internas")
EXT_LIGHTS = objs_in("12c_Luzes_Externas")
EMISSIVE = [m for m in bpy.data.materials if m.get("luz")]
_emit0 = {m.name: m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value for m in EMISSIVE}

CEILING_PREFIX = ("Forro_", "Sanca_", "LED_sanca", "Viga_eixo2", "Laje_", "Cobertura_", "Testeira_", "Spot_", "Plafon_")
_saved = {}
CUR = {}

def set_emission(factor):
    for m in EMISSIVE:
        m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = _emit0[m.name] * factor

def lights(int_on, ext_on, int_factor=1.0):
    for o in INT_LIGHTS:
        o.hide_render = not int_on
        if o.type == "LIGHT":
            o.data["e0"] = o.data.get("e0", o.data.energy)
            o.data.energy = o.data["e0"] * int_factor
    for o in EXT_LIGHTS:
        o.hide_render = not ext_on

def cutaway(on):
    """Planta 3D: remove laje/forros/peças altas e rebaixa paredes para 2,40 m."""
    for ob in bpy.data.objects:
        if ob.name.startswith("REF_") or ob.type not in ("MESH", "EMPTY", "LIGHT"):
            continue
        key = ob.name
        if on:
            _saved[key] = (ob.hide_render, tuple(ob.scale))
            colls = [c.name for c in ob.users_collection]
            bb = [ob.matrix_world @ __import__("mathutils").Vector(v) for v in ob.bound_box] if ob.type == "MESH" else None
            zmin = min(v.z for v in bb) if bb else 0
            if ob.name.startswith(CEILING_PREFIX) or "03_Estrutura_Vigas" in colls or (bb and zmin > 2.05) \
                    or "_viga" in ob.name or "_verga_" in ob.name or "Muro" in ob.name or "Portao" in ob.name \
                    or "copa" in ob.name or "galho" in ob.name or "_tronco" in ob.name and "Arvore" in (ob.parent.name if ob.parent else ""):
                ob.hide_render = True
            if "02_Paredes_e_Pilares" in colls and ob.type == "MESH":
                ob.scale = (1, 1, 2.40 / 3.20)
            if ob.name.startswith(("Armario_S", "Nicho_", "Trelica")) and ob.type == "MESH":
                ob.scale = (1, 1, 2.30 / 2.90)
            if "04_Esquadrias" in colls and ob.type == "MESH" and bb and max(v.z for v in bb) > 2.5:
                ob.scale = (1, 1, 2.40 / 2.90)
        else:
            if key in _saved:
                ob.hide_render, sc_ = _saved[key]
                ob.scale = sc_

def apply_mode(mode):
    cutaway(False)
    if mode in ("dia", "aereo", "topo"):
        lighting.world("dia"); lighting.sun("dia")
        interior = CUR.get("interior", False)
        lights(interior, False, 0.35); set_emission(0.35 if interior else 0.2)
        sc.view_settings.exposure = 0.55 if interior else -0.95
    elif mode in ("tarde", "aereo_tarde"):
        lighting.world("tarde"); lighting.sun("tarde")
        lights(True, True); set_emission(1.0)
        sc.view_settings.exposure = 0.4
    elif mode == "tarde_int":
        lighting.world("tarde"); lighting.sun("tarde")
        lights(True, False, 0.8); set_emission(1.0)
        sc.view_settings.exposure = 0.4
    elif mode == "banho":   # ambientes sem janela: luz artificial completa
        lighting.world("dia"); lighting.sun("dia")
        lights(True, False, 1.0); set_emission(1.0)
        sc.view_settings.exposure = -0.15
    elif mode in ("planta", "planta_persp"):
        lighting.world("dia"); lighting.sun("dia")
        lights(False, False); set_emission(0.0)
        cutaway(True)
        sc.view_settings.exposure = -0.8

t_all = time.time()
for cid in ids:
    c = CAMS[cid]
    cam = cams.make_camera(c, bpy.data.collections["14_Cameras"])   # sempre sincronizada com casa/cameras.py
    sc.camera = cam
    CUR["interior"] = (cid[0] in "IDKCSBX" and cid not in ("X03", "X04")) or cid == "M01"
    apply_mode(c["modo"])
    if c["modo"] in ("topo", "planta"):
        sc.render.resolution_x, sc.render.resolution_y = (3200, 3200) if c["modo"] == "planta" else (3840, 3840)
    else:
        sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
    t0 = time.time()
    sc.render.filepath = os.path.join(out, f"{cid}.{ext}")
    bpy.ops.render.render(write_still=True)
    print(f"RENDER {cid} {c['amb']} modo={c['modo']} {time.time()-t0:.1f}s")
print(f"TOTAL {time.time()-t_all:.1f}s")
