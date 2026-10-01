"""Arquitetura documentada: paredes, vãos, esquadrias, pisos, forros, laje, vigas, pilares.

Tudo vem de data/projeto.json (coordenadas já ancoradas nos eixos). Cada objeto
recebe propriedades customizadas: 'id', 'fonte', 'status' (C/G/X/H/P) e 'categoria'.
"""
import json, math, os
import bpy
from mathutils import Vector
from .core import (ROOT, coll, set_coll, box, mesh_obj, cylinder, add_bevel, sweep_profile_x,
                   transform, link, group)

DATA = json.load(open(os.path.join(ROOT, "data", "projeto.json")))

Z_SLAB_BOT = 3.20
Z_SLAB_TOP = 3.40
Z_FORRO = 3.05
Z_GLASS = 2.90
Z_DOOR = 2.10
OPEN_LEAF = {"JV-03": 2}   # folha norte do vão oeste da sala de jantar aberta (saída para a piscina)

# Ambientes para escolha de acabamento de face (retângulos internos, incluem folga)
ROOMS = {
    "jantar_cozinha": ([0.10, 8.30], [-4.75, -0.10]),
    "estar": ([0.10, 5.10], [-9.80, -4.75]),
    "corredor": ([5.10, 13.00], [-5.85, -4.75]),
    "despensa": ([6.55, 8.30], [-2.80, -1.30]),
    "wc_social": ([6.55, 8.30], [-4.65, -2.95]),
    "garagem": ([8.50, 13.20], [-4.65, 0.10]),
    "suite2": ([5.30, 8.30], [-11.05, -6.05]),
    "wc_s2": ([8.50, 9.80], [-8.50, -6.05]),
    "wc_s1": ([8.50, 9.80], [-11.25, -8.65]),
    "suite1": ([10.00, 13.00], [-11.05, -6.05]),
    "servico": ([0.90, 4.30], [-10.50, -10.00]),
}
# ordem de prioridade (salas menores primeiro, pois retângulos se sobrepõem)
ROOM_ORDER = ["despensa", "wc_social", "wc_s2", "wc_s1", "servico", "garagem", "suite2", "suite1",
              "corredor", "estar", "jantar_cozinha"]

def room_at(x, y):
    for r in ROOM_ORDER:
        (x0, x1), (y0, y1) = ROOMS[r]
        if x0 - 1e-4 <= x <= x1 + 1e-4 and y0 - 1e-4 <= y <= y1 + 1e-4:
            return r
    return None

FOOTPRINT = [([-0.10, 13.20], [-11.25, 0.10]), ([8.30, 10.00], [-11.45, -11.25]), ([0.70, 4.50], [-10.60, -9.80])]
def inside_footprint(x, y):
    return any(a[0] <= x <= a[1] and b[0] <= y <= b[1] for a, b in FOOTPRINT)

def wall_face_material(L, x, y, z):
    r = room_at(x, y)
    if r in ("wc_s2", "wc_s1", "wc_social"):
        return L["parede_banho"]
    if r == "suite2":
        return L["parede_rosa"]
    if r in ("garagem", "servico"):
        return L["parede_ext"]
    if r is not None:
        return L["parede_int"]
    if inside_footprint(x, y):
        return L["parede_int"]
    return L["parede_ext"]

def assign_face_materials(ob, L):
    """Escolhe o acabamento de cada face pelo ambiente para onde a face aponta."""
    me = ob.data
    mats = []
    def mi(m):
        if m.name not in [x.name for x in me.materials]:
            me.materials.append(m)
        return [x.name for x in me.materials].index(m.name)
    for p in me.polygons:
        c = ob.matrix_world @ p.center
        n = p.normal
        if abs(n.z) > 0.9:
            p.material_index = mi(L["parede_int"]); continue
        q = c + n * 0.06
        p.material_index = mi(wall_face_material(L, q.x, q.y, q.z))

# ---------------------------------------------------------------- vãos
def openings_on(wall):
    """Vãos (portas/vidros) contidos em uma parede: devolve (eixo_longo, [(a,b,z0,z1,id)])."""
    (x0, x1), (y0, y1) = wall["x"], wall["y"]
    along_x = (x1 - x0) >= (y1 - y0)
    res = []
    for d in DATA["esquadrias"]["portas"]:
        if along_x and isinstance(d.get("y"), (int, float)) and isinstance(d.get("x"), list):
            if y0 <= d["y"] <= y1 and d["x"][0] >= x0 - 1e-6 and d["x"][1] <= x1 + 1e-6:
                res.append((d["x"][0], d["x"][1], 0.0, d["altura"], d["id"]))
        if not along_x and isinstance(d.get("x"), (int, float)) and isinstance(d.get("y"), list):
            if x0 <= d["x"] <= x1 and d["y"][0] >= y0 - 1e-6 and d["y"][1] <= y1 + 1e-6:
                res.append((d["y"][0], d["y"][1], 0.0, d["altura"], d["id"]))
    return along_x, sorted(res)

def wall_with_openings(L, w):
    (x0, x1), (y0, y1) = w["x"], w["y"]
    along_x, ops = openings_on(w)
    parts = []
    zt = Z_SLAB_BOT
    if not ops:
        parts.append(box(w["id"], x0, x1, y0, y1, 0, zt, L["parede_int"]))
    else:
        a0, a1 = (x0, x1) if along_x else (y0, y1)
        cur = a0
        for (a, b, z0, z1, oid) in ops:
            if a > cur + 1e-6:
                parts.append(_seg(w["id"] + "_seg", along_x, cur, a, (x0, x1, y0, y1), 0, zt, L))
            parts.append(_seg(w["id"] + "_verga_" + oid, along_x, a, b, (x0, x1, y0, y1), z1, zt, L))
            cur = b
        if a1 > cur + 1e-6:
            parts.append(_seg(w["id"] + "_seg", along_x, cur, a1, (x0, x1, y0, y1), 0, zt, L))
    for p in parts:
        p["id"] = w["id"]; p["status"] = w["status"]; p["categoria"] = "arquitetura"
        p["fonte"] = "PDF pág. 2/23 (planta de cotas + fundação)"
        assign_face_materials(p, L)
    return parts

def _seg(name, along_x, a, b, rect, z0, z1, L):
    x0, x1, y0, y1 = rect
    if along_x:
        return box(name, a, b, y0, y1, z0, z1, L["parede_int"])
    return box(name, x0, x1, a, b, z0, z1, L["parede_int"])

# ---------------------------------------------------------------- caixilhos
def glazing(L, g, C):
    """Pano de vidro piso-teto (0–2,90) com perfis de alumínio bronze, folhas de correr."""
    objs = []
    fr = 0.05      # largura aparente do perfil
    dep = 0.10     # profundidade do marco
    z0, z1 = g["z"]
    n = g["folhas"]
    if isinstance(g["x"], list):   # vão ao longo de X, plano em y
        a0, a1 = g["x"]; c = g["y"]; along_x = True
    else:
        a0, a1 = g["y"]; c = g["x"]; along_x = False
    def B(name, a, b, d0, d1, za, zb, mat):
        if along_x:
            return box(name, a, b, c + d0, c + d1, za, zb, mat, C)
        return box(name, c + d0, c + d1, a, b, za, zb, mat, C)
    gid = g["id"]
    # marco perimetral
    objs.append(B(gid + "_marco_inf", a0, a1, -dep / 2, dep / 2, z0, z0 + 0.025, L["alu_bronze"]))
    objs.append(B(gid + "_marco_sup", a0, a1, -dep / 2, dep / 2, z1 - fr, z1, L["alu_bronze"]))
    objs.append(B(gid + "_marco_e", a0, a0 + fr, -dep / 2, dep / 2, z0, z1, L["alu_bronze"]))
    objs.append(B(gid + "_marco_d", a1 - fr, a1, -dep / 2, dep / 2, z0, z1, L["alu_bronze"]))
    W = (a1 - a0 - 2 * fr)
    if n == 1:
        objs.append(B(gid + "_vidro", a0 + fr, a1 - fr, -0.004, 0.004, z0 + 0.025, z1 - fr, L["vidro"]))
    else:
        lw = W / n + 0.03  # sobreposição das folhas
        for i in range(n):
            la = a0 + fr + i * (W / n) - (0.015 if i > 0 else 0)
            lb = min(la + lw, a1 - fr) if i < n - 1 else a1 - fr
            off = (0.022 if i % 2 == 0 else -0.022)
            if gid in OPEN_LEAF and OPEN_LEAF[gid] == i:   # folha de correr aberta (percurso da visita)
                sh = -(W / n) + 0.08 if i == n - 1 else (W / n) - 0.08
                la, lb = la + sh, lb + sh
            st = 0.04
            objs.append(B(f"{gid}_folha{i+1}_vidro", la + st, lb - st, off - 0.004, off + 0.004, z0 + 0.06, z1 - fr - 0.04, L["vidro"]))
            for nm, (aa, bb, za, zb) in {
                "esq": (la, la + st, z0 + 0.025, z1 - fr),
                "dir": (lb - st, lb, z0 + 0.025, z1 - fr),
                "inf": (la, lb, z0 + 0.025, z0 + 0.06),
                "sup": (la, lb, z1 - fr - 0.04, z1 - fr)}.items():
                objs.append(B(f"{gid}_folha{i+1}_{nm}", aa, bb, off - 0.018, off + 0.018, za, zb, L["alu_bronze"]))
            # puxador vertical embutido
            hp = la + st / 2 if i % 2 else lb - st / 2
            objs.append(B(f"{gid}_folha{i+1}_puxador", hp - 0.008, hp + 0.008, off - 0.03, off + 0.03, 0.95, 1.25, L["alu_bronze"]))
    # soleira de pedra
    objs.append(B(gid + "_soleira", a0, a1, -0.10, 0.10, -0.02, 0.002, L["travertino"]))
    # verga/viga sobre o vão (0,30 de viga 20x30 -> 2,90 a 3,20)
    objs.append(B(gid + "_viga", a0, a1, -0.10, 0.10, z1, Z_SLAB_BOT, L["parede_int"]))
    for o in objs:
        o["id"] = gid; o["status"] = g["status"]; o["categoria"] = "arquitetura"
        o["fonte"] = "PDF págs. 1, 2, 6 (fachadas, planta, cortes)"
    assign_face_materials(objs[-1], L)
    return objs

# ---------------------------------------------------------------- portas
def door(L, d, C, angle_deg=0.0, swing=None, hinge=None, style="lisa"):
    """Porta de giro com batente, guarnições, folha, dobradiças e maçaneta.

    swing: +1/-1 = lado (eixo perpendicular) para onde a folha abre.
    hinge: 'a' (início do vão) ou 'b' (fim do vão).
    """
    objs = []
    H = d["altura"]
    t_wall = 0.20 if d["id"] in ("PT-01", "PT-02", "PT-03", "PT-04", "PT-05", "PT-06") else 0.15
    if d["id"] == "PT-07":
        t_wall = 0.15
    if isinstance(d.get("x"), list):
        a0, a1 = d["x"]; c = d["y"]; along_x = True
    else:
        a0, a1 = d["y"]; c = d["x"]; along_x = False
    def B(name, a, b, p0, p1, za, zb, mat, cc=C):
        if along_x:
            return box(name, a, b, c + p0, c + p1, za, zb, mat, cc)
        return box(name, c + p0, c + p1, a, b, za, zb, mat, cc)
    bt = 0.035  # batente
    fm = L["laca_off"] if style != "entrada" else L["porta_madeira"]
    # batente (marco) em U
    objs.append(B(d["id"] + "_batente_e", a0, a0 + bt, -t_wall / 2, t_wall / 2, 0, H, fm))
    objs.append(B(d["id"] + "_batente_d", a1 - bt, a1, -t_wall / 2, t_wall / 2, 0, H, fm))
    objs.append(B(d["id"] + "_batente_sup", a0, a1, -t_wall / 2, t_wall / 2, H - bt, H, fm))
    # guarnições (alizares) nas duas faces
    gw = 0.07
    for s in (-1, 1):
        p0, p1 = (t_wall / 2, t_wall / 2 + 0.012) if s > 0 else (-t_wall / 2 - 0.012, -t_wall / 2)
        if d["id"] in ("PT-01",) and s > 0:
            continue
        objs.append(B(f"{d['id']}_guarn_e{s}", a0 - gw + bt, a0 + bt, p0, p1, 0, H + gw - bt, fm))
        objs.append(B(f"{d['id']}_guarn_d{s}", a1 - bt, a1 + gw - bt, p0, p1, 0, H + gw - bt, fm))
        objs.append(B(f"{d['id']}_guarn_s{s}", a0 - gw + bt, a1 + gw - bt, p0, p1, H - bt, H + gw - bt, fm))
    # soleira
    objs.append(B(d["id"] + "_soleira", a0, a1, -t_wall / 2, t_wall / 2, -0.02, 0.003, L["travertino"]))
    # folha (desenhada fechada com origem na dobradiça; depois rotacionada)
    lw = (a1 - a0) - 2 * bt - 0.006
    lt = 0.038
    leaf_mat = L["porta_madeira"]
    sw = swing if swing is not None else 1
    hg = hinge or "a"
    leaf_parts = []
    # folha em coordenadas locais: dobradiça na origem, folha ao longo de +X local
    def LB(name, u0, u1, v0, v1, za, zb, mat):
        return box(name, u0, u1, v0, v1, za, zb, mat, C)
    leaf_parts.append(LB(d["id"] + "_folha", 0, lw, -lt / 2, lt / 2, 0.008, H - bt - 0.004, leaf_mat))
    if style == "entrada":
        # frisos verticais em baixo-relevo + puxador longo de latão
        for k in range(1, 6):
            u = lw * k / 6
            leaf_parts.append(LB(f"{d['id']}_friso{k}", u - 0.004, u + 0.004, -lt / 2 - 0.002, lt / 2 + 0.002, 0.15, H - 0.2, L["nogueira"]))
        for s in (-1, 1):
            v = s * (lt / 2 + 0.04)
            leaf_parts.append(LB(f"{d['id']}_puxador{s}", lw - 0.14, lw - 0.115, v - 0.012, v + 0.012, 0.7, 1.9, L["latao"]))
            leaf_parts.append(LB(f"{d['id']}_puxsup{s}", lw - 0.14, lw - 0.115, min(0, v) if s < 0 else 0, max(0, v), 1.86, 1.89, L["latao"]))
            leaf_parts.append(LB(f"{d['id']}_puxinf{s}", lw - 0.14, lw - 0.115, min(0, v) if s < 0 else 0, max(0, v), 0.71, 0.74, L["latao"]))
    elif style == "veneziana":
        n = int((H - 0.3) / 0.06)
        for k in range(n):
            z = 0.15 + k * 0.06
            leaf_parts.append(LB(f"{d['id']}_aleta{k}", 0.06, lw - 0.06, -0.012, 0.012, z, z + 0.035, L["veneziana"]))
        leaf_parts[0].data.materials[0] = L["veneziana"]
        # transforma a folha principal em requadro: substitui por 4 montantes
        bpy.data.objects.remove(leaf_parts[0], do_unlink=True)
        leaf_parts = leaf_parts[1:]
        for nm, (u0, u1, z0, z1) in {"me": (0, 0.06, 0.008, H - bt), "md": (lw - 0.06, lw, 0.008, H - bt),
                                      "ti": (0, lw, 0.008, 0.15), "ts": (0, lw, H - bt - 0.12, H - bt)}.items():
            leaf_parts.append(LB(f"{d['id']}_{nm}", u0, u1, -lt / 2, lt / 2, z0, z1, L["veneziana"]))
    else:
        # porta lisa com almofadas (frisos) clássicos e maçaneta alavanca latão
        for (z0, z1) in ((0.18, 0.95), (1.10, H - 0.22)):
            for s in (-1, 1):
                v0 = lt / 2 if s > 0 else -lt / 2 - 0.006
                v1 = v0 + 0.006
                u0, u1 = 0.14, lw - 0.14
                for nm, (aa, bb, za, zb) in {"l": (u0, u0 + 0.018, z0, z1), "r": (u1 - 0.018, u1, z0, z1),
                                              "b": (u0, u1, z0, z0 + 0.018), "t": (u0, u1, z1 - 0.018, z1)}.items():
                    leaf_parts.append(LB(f"{d['id']}_mold{nm}{s}{z0}", aa, bb, v0, v1, za, zb, leaf_mat))
        for s in (-1, 1):
            v = s * (lt / 2 + 0.03)
            leaf_parts.append(cylinder(f"{d['id']}_roseta{s}", 0.025, 0.012, (lw - 0.065, s * lt / 2, 1.0), 24, L["latao"], C, axis="Y"))
            leaf_parts[-1].location.y = 0
            leaf_parts.append(LB(f"{d['id']}_macaneta{s}", lw - 0.19, lw - 0.06, v - 0.009, v + 0.009, 0.99, 1.01, L["latao"]))
            leaf_parts.append(LB(f"{d['id']}_haste{s}", lw - 0.075, lw - 0.055, min(s * lt / 2, v), max(s * lt / 2, v), 0.99, 1.01, L["latao"]))
    for k, z in enumerate((0.25, H / 2, H - 0.3)):
        leaf_parts.append(cylinder(f"{d['id']}_dobradica{k}", 0.008, 0.10, (0, 0, z - 0.05), 12, L["latao"], C))
    # posicionamento: pivô no canto da folha do lado da abertura
    if along_x:
        if hg == "a":
            px, rot0 = a0 + bt + 0.003, 0.0
        else:
            px, rot0 = a1 - bt - 0.003, math.pi
        pivot = (px, c + sw * (t_wall / 2 - lt / 2 - 0.005), 0)
        dir_vec = Vector((1, 0, 0)) if hg == "a" else Vector((-1, 0, 0))
        swing_vec = Vector((0, sw, 0))
    else:
        if hg == "a":
            py, rot0 = a0 + bt + 0.003, math.pi / 2
        else:
            py, rot0 = a1 - bt - 0.003, -math.pi / 2
        pivot = (c + sw * (t_wall / 2 - lt / 2 - 0.005), py, 0)
        dir_vec = Vector((0, 1, 0)) if hg == "a" else Vector((0, -1, 0))
        swing_vec = Vector((sw, 0, 0))
    sign = 1 if dir_vec.cross(swing_vec).z > 0 else -1
    pv = bpy.data.objects.new(d["id"] + "_pivo_folha", None)
    pv.empty_display_size = 0.2
    link(pv, C)
    for o in leaf_parts:
        o.parent = pv
    pv.location = pivot
    pv.rotation_euler = (0, 0, rot0 + sign * math.radians(angle_deg))
    pv["abertura_graus"] = angle_deg
    pv["nota"] = "Gire o eixo Z deste Empty para abrir/fechar a folha"
    for o in objs + leaf_parts + [pv]:
        o["id"] = d["id"]; o["status"] = d["status"]; o["categoria"] = "arquitetura"
        o["fonte"] = "PDF pág. 2 (vão e sentido de abertura) + cortes (altura)"
    return objs + leaf_parts

# ---------------------------------------------------------------- pisos / forros
def floors(L, C):
    o = []
    oak = L["piso_madeira"]
    o.append(box("Piso_jantar_cozinha", 0.10, 6.40, -4.75, -0.10, -0.02, 0, oak, C))
    o.append(box("Piso_passagem_despensa", 6.40, 8.30, -1.15, -0.10, -0.02, 0, oak, C))
    o.append(box("Piso_corredor", 0.10, 13.00, -5.85, -4.75, -0.02, 0, oak, C))
    o.append(box("Piso_estar", 0.10, 5.10, -9.80, -5.85, -0.02, 0, oak, C))
    o.append(box("Piso_suite2", 5.30, 8.30, -11.05, -6.05, -0.02, 0, oak, C))
    o.append(box("Piso_suite1", 10.00, 13.00, -11.05, -6.05, -0.02, 0, oak, C))
    wet = L["piso_banho"]
    o.append(box("Piso_wc_social", 6.55, 8.30, -4.65, -2.95, -0.02, 0.002, wet, C))
    o.append(box("Piso_despensa", 6.55, 8.30, -2.80, -1.30, -0.02, 0.002, wet, C))
    o.append(box("Piso_wc_suite2", 8.50, 9.80, -8.50, -6.05, -0.02, 0.002, wet, C))
    o.append(box("Piso_wc_suite1", 8.50, 9.80, -11.25, -8.65, -0.02, 0.002, wet, C))
    o.append(box("Piso_servico", 0.90, 4.30, -10.62, -10.00, -0.04, -0.02, wet, C))
    o.append(box("Piso_garagem", 8.50, 13.20, -4.65, 0.10, -0.06, -0.03, L["piso_garagem"], C))
    for x in o:
        x["categoria"] = "acabamento"; x["status"] = "P (material) / X (contorno)"
    return o

CEIL_ROOMS = [  # (nome, x, y, sanca_led)
    ("jantar_cozinha", [0.10, 5.10], [-4.75, -0.10], True),
    ("cozinha_leste", [5.30, 8.30], [-1.15, -0.10], False),
    ("cozinha_nicho", [5.30, 6.40], [-4.75, -1.15], False),
    ("estar", [0.10, 5.10], [-9.80, -4.75], True),
    ("corredor", [5.30, 13.00], [-5.85, -4.75], True),
    ("suite2", [5.30, 8.30], [-11.05, -6.05], True),
    ("suite1", [10.00, 13.00], [-11.05, -6.05], True),
    ("wc_social", [6.55, 8.30], [-4.65, -2.95], False),
    ("despensa", [6.55, 8.30], [-2.80, -1.30], False),
    ("wc_s2", [8.50, 9.80], [-8.50, -6.05], False),
    ("wc_s1", [8.50, 9.80], [-11.25, -8.65], False),
]

def ceilings(L, C, CL):
    """Forro de gesso a 3,05 (cortes) com sanca perimetral e fita LED (planta elétrica)."""
    o = []
    f = L["forro"]
    for nm, (x0, x1), (y0, y1), sanca in CEIL_ROOMS:
        if not sanca:
            o.append(box("Forro_" + nm, x0, x1, y0, y1, Z_FORRO, Z_FORRO + 0.02, f, C))
            continue
        b = 0.28; g = 0.06
        o.append(box("Forro_" + nm, x0 + b + g, x1 - b - g, y0 + b + g, y1 - b - g, Z_FORRO, Z_FORRO + 0.02, f, C))
        # sanca rebaixada 10 cm (2,95) — também esconde trilho de cortina junto aos vidros
        zb = Z_FORRO - 0.10
        o.append(box("Sanca_" + nm + "_N", x0, x1, y1 - b, y1, zb, Z_FORRO + 0.02, f, C))
        o.append(box("Sanca_" + nm + "_S", x0, x1, y0, y0 + b, zb, Z_FORRO + 0.02, f, C))
        o.append(box("Sanca_" + nm + "_O", x0, x0 + b, y0 + b, y1 - b, zb, Z_FORRO + 0.02, f, C))
        o.append(box("Sanca_" + nm + "_L", x1 - b, x1, y0 + b, y1 - b, zb, Z_FORRO + 0.02, f, C))
        # fecho superior da fenda (acima do LED) para não vazar luz para a laje
        o.append(box("Forro_topo_" + nm, x0 + b, x1 - b, y0 + b, y1 - b, Z_FORRO + 0.10, Z_FORRO + 0.12, f, C))
        # fita LED escondida sobre a borda interna da sanca
        led = L["led"]
        e = 0.012
        for side, (ax0, ax1, ay0, ay1) in {
            "N": (x0 + b, x1 - b, y1 - b - e, y1 - b), "S": (x0 + b, x1 - b, y0 + b, y0 + b + e),
            "O": (x0 + b, x0 + b + e, y0 + b, y1 - b), "L": (x1 - b - e, x1 - b, y0 + b, y1 - b)}.items():
            lo = box(f"LED_sanca_{nm}_{side}", ax0, ax1, ay0, ay1, Z_FORRO + 0.02, Z_FORRO + 0.03, led, CL)
            lo["categoria"] = "iluminacao"; lo["fonte"] = "Planta elétrica pág. 5 (LEDs)"
            o.append(lo)
    # viga do eixo 2 revestida em gesso sob o forro (corte A/A mostra o forro contornando a viga)
    o.append(box("Viga_eixo2_revestida", 5.10, 5.30, -5.85, -0.10, 2.90, Z_FORRO, f, C))
    for x in o:
        x.setdefault("categoria", "acabamento") if hasattr(x, "setdefault") else None
        if "categoria" not in x:
            x["categoria"] = "acabamento"
        x["status"] = "C (nível 3,05) / H (desenho da sanca)"
    return o

def slab_and_roof(L, C):
    o = []
    s = DATA["laje_cobertura"]
    (x0, x1), (y0, y1) = s["x"], s["y"]
    o.append(box("Laje_macica_cobertura", x0, x1, y0, y1, Z_SLAB_BOT, Z_SLAB_TOP, L["laje"], C))
    o[-1]["status"] = s["status"]; o[-1]["id"] = "LAJE"
    # regularização com caimento 1% em 4 águas + impermeabilização (H)
    cx = (x0 + x1) / 2
    ry0 = y0 + (y1 - y0) / 2; half = (y1 - y0) / 2
    h = 0.01 * half
    v = [(x0, y0, Z_SLAB_TOP), (x1, y0, Z_SLAB_TOP), (x1, y1, Z_SLAB_TOP), (x0, y1, Z_SLAB_TOP),
         (x0 + half, ry0, Z_SLAB_TOP + h), (x1 - half, ry0, Z_SLAB_TOP + h)]
    f = [(0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4)]
    r = mesh_obj("Cobertura_regularizacao_4aguas", v, f, L["impermeab"], C)
    r["status"] = "H (caimento 1% — PDF diz apenas 'levemente acentuada')"
    o.append(r)
    # testeira/pingadeira (acabamento da borda da laje)
    t = 0.02
    for nm, (a, b, c, d) in {"N": (x0 - t, x1 + t, y1, y1 + t), "S": (x0 - t, x1 + t, y0 - t, y0),
                             "O": (x0 - t, x0, y0, y1), "L": (x1, x1 + t, y0, y1)}.items():
        o.append(box("Testeira_" + nm, a, b, c, d, Z_SLAB_BOT - 0.03, Z_SLAB_TOP + 0.03, L["laca_branca"], C))
    # forro do beiral (face inferior pintada) — mesma laje, só material
    for x in o:
        x["categoria"] = "arquitetura"
    return o

from .estrutura import BEAMS, COLUMNS

def structure(L, C):
    """Vigas e pilares (pág. 23 + cortes). Na maior parte embutidos nas paredes."""
    o = []
    for nm, x0, x1, y0, y1 in BEAMS:
        e = 0.01  # recuo para não coincidir com as faces das paredes
        b = box(nm, x0 + e, x1 - e, y0 + e, y1 - e, 2.905, Z_SLAB_BOT - 0.002, L["forro"], C)  # vigas revestidas/pintadas como o forro
        b["categoria"] = "estrutura"; b["status"] = "C seção 20x30 / G traçado"; b["fonte"] = "Pág. 23 e cortes pág. 6"
        o.append(b)
    for nm, x, y, dx, dy in COLUMNS:
        x0, x1 = x - dx / 2, x + dx / 2
        y0, y1 = y - dy / 2, y + dy / 2
        # pilares da garagem ficam com faces alinhadas às paredes desenhadas
        if nm == "P_A7":
            x0, x1, y0, y1 = 12.80, 13.20, -0.10, 0.10
        p = box(nm, x0 + 0.01, x1 - 0.01, y0 + 0.01, y1 - 0.01, 0.005, Z_SLAB_BOT - 0.002, L["laje"], C)
        p["categoria"] = "estrutura"; p["status"] = "C seção / C eixos"; p["fonte"] = "Pág. 23"
        o.append(p)
    return o

def baseboards(L, C, wall_objs):
    """Rodapé 10 cm laqueado nas faces de parede voltadas a ambientes secos."""
    o = []
    rm = L["laca_branca"]
    for w in wall_objs:
        if w.data.polygons and w.name.find("verga") >= 0:
            continue
        for p in w.data.polygons:
            n = p.normal
            if abs(n.z) > 0.5:
                continue
            c = w.matrix_world @ p.center
            q = c + n * 0.06
            r = room_at(q.x, q.y)
            if r is None or r in ("wc_s1", "wc_s2", "wc_social", "garagem", "servico", "despensa"):
                continue
            vs = [w.matrix_world @ w.data.vertices[i].co for i in p.vertices]
            zs = [v.z for v in vs]
            if min(zs) > 0.05:
                continue
            xs = [v.x for v in vs]; ys = [v.y for v in vs]
            t = 0.014
            if abs(n.x) > 0.5:
                x = c.x
                xa, xb = (x, x + t) if n.x > 0 else (x - t, x)
                o.append(box("Rodape_" + w.name, xa, xb, min(ys), max(ys), 0, 0.10, rm, C))
            else:
                y = c.y
                ya, yb = (y, y + t) if n.y > 0 else (y - t, y)
                o.append(box("Rodape_" + w.name, min(xs), max(xs), ya, yb, 0, 0.10, rm, C))
            o[-1]["categoria"] = "acabamento"; o[-1]["status"] = "P"
    return o

def facade_details(L, C):
    """Frisos verticais da parede leste da suíte 1, desenhados no Alçado Frontal (pág. 1):
    juntas a cada ~1,02 m (medidas na fachada, status X). Ripado na parede oeste da garagem:
    PROPOSTA inspirada na hachura das fachadas."""
    from .mats import pbr
    fr = pbr("Friso (junta) da fachada", (0.45, 0.43, 0.40), 0.9, categoria="arquitetura")
    o = []
    for k, y in enumerate((-10.71, -9.70, -8.67, -7.66, -6.65)):
        b = box(f"Friso_fachada_leste_{k}", 13.200, 13.206, y - 0.012, y + 0.012, 0.0, 3.20, fr, C)
        b["status"] = "X — juntas desenhadas no Alçado Frontal"; b["categoria"] = "arquitetura"
        o.append(b)
    n = int((4.65 - 1.25) / 0.06)
    for k in range(n):
        y = -4.62 + k * 0.06
        b = box(f"Ripado_garagem_{k}", 8.50, 8.53, y, y + 0.04, 0.0, 2.88, L["carvalho"], C)
        b["status"] = "P"; b["categoria"] = "proposta"
        o.append(b)
    return o

def build(L):
    root = coll("CASA")
    CW = coll("02_Paredes_e_Pilares", root)
    CE = coll("03_Estrutura_Vigas", root)
    CJ = coll("04_Esquadrias", root)
    CP = coll("05_Pisos_e_Forros", root)
    CL = coll("12_Iluminacao", root)
    CR = coll("06_Laje_e_Cobertura", root)
    set_coll(CW)
    walls = []
    for w in DATA["paredes"]["lista"]:
        walls += wall_with_openings(L, w)
    set_coll(CE)
    structure(L, CE)
    set_coll(CJ)
    for g in DATA["esquadrias"]["panos_de_vidro"]:
        glazing(L, g, CJ)
    # portas — ângulo de abertura escolhido para a visita (editável no Empty *_pivo_folha)
    P = {d["id"]: d for d in DATA["esquadrias"]["portas"]}
    door(L, P["PT-01"], CJ, 82, swing=-1, hinge="b", style="entrada")   # abre p/ dentro (oeste), dobradiça norte
    door(L, P["PT-02"], CJ, 88, swing=-1, hinge="b")                    # suite 2: dobradiça leste, abre p/ sul
    door(L, P["PT-03"], CJ, 88, swing=-1, hinge="a")                    # suite 1: dobradiça oeste
    door(L, P["PT-04"], CJ, 70, swing=1, hinge="a")                     # WC s2: dobradiça sul, abre p/ leste
    door(L, P["PT-05"], CJ, 70, swing=-1, hinge="a")                    # WC s1: dobradiça sul, abre p/ oeste
    door(L, P["PT-06"], CJ, 35, swing=1, hinge="a")                     # WC social: dobradiça oeste, abre p/ norte
    door(L, P["PT-07"], CJ, 0, swing=-1, hinge="b")                     # despensa: dobradiça leste, abre p/ sul
    door(L, dict(P["PT-08"], x=[0.90, 1.90], id="PT-08a"), CJ, 100, swing=-1, hinge="a", style="veneziana")
    door(L, dict(P["PT-08"], x=[1.90, 2.90], id="PT-08b"), CJ, 100, swing=-1, hinge="b", style="veneziana")
    door(L, P["PT-09"], CJ, 0, swing=-1, hinge="b", style="veneziana")
    set_coll(CP)
    floors(L, CP)
    ceilings(L, CP, CL)
    baseboards(L, CP, walls)
    set_coll(CR)
    slab_and_roof(L, CR)
    set_coll(CW)
    facade_details(L, CW)
    return walls
