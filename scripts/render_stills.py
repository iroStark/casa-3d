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

CEILING_PREFIX = ("Forro_", "Sanca_", "LED_sanca", "Perfil_LED", "LED_perfil", "Painel_LED", "Viga_eixo2", "Laje_", "Cobertura_", "Testeira_", "Spot_", "Plafon_")
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

_hid = {}
def esconder(objs):
    for o in objs:
        if o.name not in _hid:
            _hid[o.name] = o.hide_render
        o.hide_render = True

def restaurar():
    for n, v in _hid.items():
        o = bpy.data.objects.get(n)
        if o:
            o.hide_render = v
    _hid.clear()
    for cn in ("15_Cotas_Alcados", "15_Cotas_Cortes", "15_Rotulos_Planta", "15_Cotas_Planta"):
        c = bpy.data.collections.get(cn)
        if c:
            c.hide_render = True
    cs = bpy.data.objects.get("Captador_sombra_pranchas")
    if cs:
        cs.hide_render = True
    sc.render.film_transparent = False

def em_colecao(prefixos):
    return [o for o in bpy.data.objects if any(c.name.startswith(prefixos) for c in o.users_collection)]

def mostrar_cotas(pai, sub):
    c = bpy.data.collections.get(pai)
    c.hide_render = False
    for ch in c.children:
        ch.hide_render = (ch.name != sub)

def sol_frontal(d):
    """Sol vindo de trás da câmera, 35° à esquerda e 40° de altura, para iluminar a fachada."""
    from mathutils import Vector, Matrix
    s_ = bpy.data.objects["Sol"]
    v = Matrix.Rotation(math.radians(35), 3, "Z") @ Vector(d)
    v = Vector((v.x * math.cos(math.radians(40)), v.y * math.cos(math.radians(40)), -math.sin(math.radians(40))))
    s_.rotation_euler = v.to_track_quat("-Z", "Y").to_euler()

def apply_mode(mode):
    cutaway(False)
    restaurar()
    if mode in ("elev", "corte"):
        lighting.world("dia"); lighting.sun("dia")
        c = CUR["cam"]
        from mathutils import Vector
        d = (Vector(c["alvo"]) - Vector(c["loc"])); d.z = 0; d.normalize()
        sol_frontal(d)
        esconder([o for o in em_colecao(("01_", "01b_", "01c_", "11_")) if not o.name.startswith("Vaso_palmeira_fachada")]
                 + [o for o in bpy.data.objects if o.name.startswith("Balizador")])
        if mode == "elev":
            mostrar_cotas("15_Cotas_Alcados", "15a_Cotas_" + c["vista"])
            lights(False, False); set_emission(0.2)
        else:
            mostrar_cotas("15_Cotas_Cortes", "15b_Cotas_" + c["vista"])
            lights(True, False, 0.6); set_emission(0.6)
        bpy.data.objects["Captador_sombra_pranchas"].hide_render = False
        sc.render.film_transparent = True
        sc.view_settings.exposure = -0.7 if mode == "elev" else 0.0
        return
    if mode == "planta_cotada":
        lighting.world("dia"); lighting.sun("dia")
        lights(False, False); set_emission(0.0)
        cutaway(True)
        bpy.data.collections["15_Cotas_Planta"].hide_render = False
        sc.view_settings.exposure = -0.8
        return
    if mode == "planta_vazia":
        lighting.world("dia"); lighting.sun("dia")
        lights(False, False); set_emission(0.0)
        cutaway(True)
        esconder(em_colecao(("09",)))
        bpy.data.collections["15_Rotulos_Planta"].hide_render = False
        sc.view_settings.exposure = -0.8
        return
    if mode in ("dia", "aereo", "topo"):
        lighting.world("dia"); lighting.sun("dia")
        interior = CUR.get("interior", False)
        lights(interior, False, 0.35); set_emission(0.35 if interior else 0.2)
        extra = 0.6 if CUR["cam"]["id"] in ("C01", "C02") else 0.0   # corredor sem janela
        sc.view_settings.exposure = (0.75 + extra) if interior else -0.85
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

# imagens fixas: porta de entrada fechada (no vídeo do percurso ela fica aberta)
_pv = bpy.data.objects.get("PT-01_pivo_folha")
if _pv is not None and "rot_fechada" in _pv:
    _pv.rotation_euler.z = _pv["rot_fechada"]
t_all = time.time()
for cid in ids:
    c = CAMS[cid]
    if "--pular-existentes" in argv and os.path.exists(os.path.join(out, f"{cid}.{ext}")):
        continue
    cam = cams.make_camera(c, bpy.data.collections["14_Cameras"])   # sempre sincronizada com casa/cameras.py
    sc.camera = cam
    CUR["interior"] = (cid[0] in "IDKCSBXV" and cid not in ("X03", "X04", "V02", "V03", "V04", "V05", "V06") and not cid.startswith("CT")) or cid == "M01"
    CUR["cam"] = c
    apply_mode(c["modo"])
    if c["modo"] in ("elev", "corte"):
        sc.render.resolution_x, sc.render.resolution_y = 3840, 1600
    elif c["modo"] in ("planta_vazia", "planta_cotada"):
        sc.render.resolution_x, sc.render.resolution_y = 3600, 3600
    elif c["modo"] in ("topo", "planta"):
        sc.render.resolution_x, sc.render.resolution_y = (3200, 3200) if c["modo"] == "planta" else (3840, 3840)
    else:
        sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
    t0 = time.time()
    sc.render.filepath = os.path.join(out, f"{cid}.{ext}")
    bpy.ops.render.render(write_still=True)
    print(f"RENDER {cid} {c['amb']} modo={c['modo']} {time.time()-t0:.1f}s")
restaurar()
print(f"TOTAL {time.time()-t_all:.1f}s")
