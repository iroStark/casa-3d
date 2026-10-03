"""Luz natural (céu físico + sol) e artificial (pontos da planta elétrica, pág. 5).

Coleções:
  13_Sol_e_Ceu            — sol (dia/entardecer comutado pelo script de render)
  12b_Luzes_Internas      — spots/pendentes/abajures (2700 K)
  12c_Luzes_Externas      — beiral, piscina, jardim
"""
import math
import bpy
from mathutils import Vector, Euler
from .core import coll, set_coll, cylinder, box, link

WARM = (1.0, 0.76, 0.52)

def world(kind="dia"):
    w = bpy.data.worlds.get("Ceu") or bpy.data.worlds.new("Ceu")
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_disc = True
    if kind == "dia":
        sky.sun_elevation = math.radians(48)
        sky.sun_rotation = math.radians(150)   # sol a noroeste (hemisfério sul, tarde)
        sky.air_density = 1.0; sky.aerosol_density = 1.2
        bg.inputs["Strength"].default_value = 0.26
    else:
        sky.sun_elevation = math.radians(1.5)
        sky.sun_rotation = math.radians(185)
        sky.air_density = 1.6; sky.aerosol_density = 3.0
        bg.inputs["Strength"].default_value = 0.30
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bpy.context.scene.world = w
    w["modo"] = kind
    return w, sky

def sun(kind="dia"):
    s = bpy.data.objects.get("Sol")
    if s is None:
        d = bpy.data.lights.new("Sol", "SUN")
        s = bpy.data.objects.new("Sol", d)
        link(s, coll("13_Sol_e_Ceu"))
    d = s.data
    if kind == "dia":
        el, az = 48, 150
        d.energy = 3.6; d.color = (1.0, 0.94, 0.86); d.angle = math.radians(0.6)
    else:
        el, az = 1.5, 185
        d.energy = 0.9; d.color = (1.0, 0.55, 0.3); d.angle = math.radians(1.5)
    # a direção da luz do sol (do céu) — alinhada ao céu físico
    s.rotation_euler = Euler((math.radians(90 - el), 0, math.radians(az + 90)), "XYZ")
    return s

def spot(name, loc, power=18.0, size_deg=75, color=WARM, C=None, blend=0.7, radius=0.03, target=None):
    d = bpy.data.lights.new(name, "SPOT")
    d.energy = power; d.color = color
    d.spot_size = math.radians(size_deg); d.spot_blend = blend
    d.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, d)
    ob.location = loc
    if target is not None:
        v = Vector(target) - Vector(loc)
        ob.rotation_euler = v.to_track_quat("-Z", "Y").to_euler()
    link(ob, C)
    return ob

def point(name, loc, power=15.0, color=WARM, C=None, radius=0.05):
    d = bpy.data.lights.new(name, "POINT")
    d.energy = power; d.color = color; d.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, d)
    ob.location = loc
    link(ob, C)
    return ob

def area(name, loc, size, power, color=WARM, C=None, rot=(0, 0, 0)):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = power; d.color = color; d.size = size[0]; d.shape = "RECTANGLE"; d.size_y = size[1]
    ob = bpy.data.objects.new(name, d)
    ob.location = loc; ob.rotation_euler = rot
    link(ob, C)
    return ob

# Pontos de luz no teto (planta elétrica pág. 5, posições aproximadas por ambiente)
DOWNLIGHTS = {
    "estar": [(1.30, -6.55), (3.90, -6.55), (1.30, -9.10), (3.90, -9.10)],
    "jantar": [(0.90, -1.20), (0.90, -4.20)],
    "cozinha": [(4.05, -2.75), (4.05, -3.85), (5.55, -1.90), (5.55, -3.60), (7.40, -0.60)],
    "corredor": [(6.40, -5.35), (8.40, -5.35), (10.40, -5.35), (12.40, -5.35)],
    "suite2": [(6.0, -6.9), (7.6, -6.9), (6.0, -10.3), (7.6, -10.3)],
    "suite1": [(10.7, -6.9), (12.3, -6.9), (10.7, -10.3), (12.3, -10.3)],
    "wc_s2": [(9.15, -7.95)],
    "wc_s1": [(9.15, -10.55)],
    "wc_social": [(7.4, -3.8)],
    "despensa": [(7.4, -2.05)],
}
GARAGE = [(9.6, -1.2), (11.8, -1.2), (9.6, -3.4), (11.8, -3.4)]

def build(L):
    M = L
    root = coll("CASA")
    CI = coll("12b_Luzes_Internas", root)
    CX = coll("12c_Luzes_Externas", root)
    CS = coll("13_Sol_e_Ceu", root)
    set_coll(coll("12_Iluminacao", root))
    for room, pts in DOWNLIGHTS.items():
        z = 3.05 if room not in () else 3.05
        for k, (x, y) in enumerate(pts):
            ring = cylinder(f"Spot_{room}_{k}_aro", 0.045, 0.006, (x, y, z - 0.006), 24, M["alu_preto"])
            disc = cylinder(f"Spot_{room}_{k}_difusor", 0.03, 0.002, (x, y, z - 0.008), 24, M["led"])
            disc["luz"] = 1
            pw = 22.0 if room.startswith("wc") or room == "despensa" else 14.0
            spot(f"L_spot_{room}_{k}", (x, y, z - 0.012), pw, 80, C=CI, radius=0.02)
    # painéis difusos de teto nos ambientes sem janela (banheiros e despensa)
    for nm, (x, y, w, d) in {"wc_s2": (9.15, -7.30, 0.60, 0.40), "wc_s1": (9.15, -9.95, 0.60, 0.40),
                             "wc_social": (7.42, -3.65, 0.60, 0.40), "despensa": (7.42, -2.05, 0.50, 0.40)}.items():
        pn = box(f"Painel_LED_{nm}", x - w / 2, x + w / 2, y - d / 2, y + d / 2, 3.035, 3.05, M["led"])
        pn["luz"] = 1
        area(f"L_painel_{nm}", (x, y, 3.03), (w, d), 45.0, C=CI)
    for k, (x, y) in enumerate(GARAGE):
        box(f"Plafon_garagem_{k}", x - 0.08, x + 0.08, y - 0.08, y + 0.08, 3.17, 3.20, M["led"])
        spot(f"L_garagem_{k}", (x, y, 3.16), 22, 100, C=CI, radius=0.05)
    # luz de sanca (complementa a emissão da fita LED, que no render já ilumina)
    # pendentes e abajures: ponto de luz no interior de cada lâmpada emissiva
    for ob in list(bpy.data.objects):
        if ob.get("luz") and "lampada" in ob.name:
            loc = ob.matrix_world.translation if ob.parent is None else None
    bpy.context.view_layer.update()
    for ob in list(bpy.data.objects):
        if ob.get("luz") and "lampada" in ob.name.lower():
            p = ob.matrix_world.translation.copy()
            pw = 6.0 if "globo" in ob.name or "Pendente" in ob.name else 10.0
            point("L_" + ob.name, p, pw, C=CI, radius=0.02)
    # luzes do beiral (pontos externos na planta elétrica): a cada ~2,2 m, 0,55 m fora das paredes
    pts = []
    for x in [0.9, 3.1, 5.3, 7.5, 9.7, 11.9]:
        pts.append((x, 0.62))
    for y in [-1.5, -3.7, -5.9, -8.1, -10.3]:
        pts.append((-0.62, y))
    for x in [1.4, 3.4, 6.6, 8.8, 11.3, 12.7]:
        pts.append((x, -11.80))
    for y in [-6.7, -8.6, -10.5]:
        pts.append((13.80, y))
    pts.append((13.80, -5.35))
    for k, (x, y) in enumerate(pts):
        cylinder(f"Spot_beiral_{k}_aro", 0.045, 0.006, (x, y, 3.194), 24, M["alu_preto"])
        d = cylinder(f"Spot_beiral_{k}_difusor", 0.03, 0.002, (x, y, 3.192), 24, M["led"]); d["luz"] = 1
        spot(f"L_beiral_{k}", (x, y, 3.185), 30, 60, C=CX, radius=0.02)
    # piscina: 3 refletores subaquáticos na parede leste
    for k, y in enumerate((-2.0, -4.85, -7.7)):
        spot(f"L_piscina_{k}", (-4.13, y, -0.55), 120, 120, color=(0.9, 0.95, 1.0), C=CX, radius=0.05, target=(-6.6, y, -1.2))
    # balizadores no jardim
    for k, (x, y) in enumerate([(-7.2, 1.2), (-7.2, -10.9), (15.0, -7.95), (14.95, -10.4), (17.0, 2.5), (-5.8, -13.0)]):
        cylinder(f"Balizador_{k}", 0.05, 0.62, (x, y, -0.22), 16, M["alu_preto"])
        d = cylinder(f"Balizador_{k}_luz", 0.045, 0.03, (x, y, 0.38), 16, M["led"]); d["luz"] = 1
        point(f"L_balizador_{k}", (x, y, 0.45), 4, C=CX, radius=0.03)
    # árvores com uplight
    for k, (x, y) in enumerate([(1.5, 5.3), (3.0, -15.7), (18.4, -14.2), (-6.8, 4.6)]):
        spot(f"L_arvore_{k}", (x + 0.6, y - 0.6, 0.05), 60, 50, C=CX, radius=0.05, target=(x, y, 4.0))
    set_coll(CS)
    world("dia")
    sun("dia")
