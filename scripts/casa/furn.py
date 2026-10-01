"""Biblioteca paramétrica de mobiliário e objetos (proposta de ambientação).

Cada função constrói o móvel em coordenadas locais (origem no centro da base,
frente voltada para -Y local) e devolve um Empty pai posicionado/rotacionado.
Assim cada peça fica editável e movível como um conjunto no .blend.
"""
import math, random
import bpy, bmesh
from mathutils import Vector, Matrix
from .core import (box, cylinder, sphere, torus, mesh_obj, add_bevel, smooth_angle,
                   group, extrude_profile, link)

R = random.Random(612)

def rb(name, x0, x1, y0, y1, z0, z1, mat, r=0.01, seg=3):
    return box(name, x0, x1, y0, y1, z0, z1, mat, bevel=r, seg=seg)

def place(name, objs, loc, rot_deg=0.0, cat="proposta", nota=None):
    e = group(name, objs, origin=loc, rot_z=math.radians(rot_deg))
    e["categoria"] = cat
    e["status"] = "P"
    if nota:
        e["nota"] = nota
    for o in objs:
        if o is not None:
            o["categoria"] = cat
    return e

def cushion(name, w, d, h, mat, loc=(0, 0, 0), r=None, tilt=0.0):
    r = r if r is not None else min(w, d, h) * 0.35
    o = box(name, -w / 2, w / 2, -d / 2, d / 2, -h / 2, h / 2, mat, bevel=r, seg=4)
    o.location = loc
    o.rotation_euler = (tilt, 0, 0)
    # leve "estofamento" no topo
    sub = o.modifiers.new("Sub", "SUBSURF"); sub.levels = 1; sub.render_levels = 2
    return o

def annulus(name, r0, r1, a0, a1, z0, z1, mat, seg=48, bevel=0.0):
    """Setor de coroa circular extrudado (sofá curvo, bancadas curvas)."""
    vs, fs = [], []
    n = seg + 1
    for i in range(n):
        a = a0 + (a1 - a0) * i / seg
        c, s = math.cos(a), math.sin(a)
        vs += [(r0 * c, r0 * s, z0), (r1 * c, r1 * s, z0), (r1 * c, r1 * s, z1), (r0 * c, r0 * s, z1)]
    for i in range(seg):
        b, nb = 4 * i, 4 * (i + 1)
        for k in range(4):
            k2 = (k + 1) % 4
            fs.append((b + k, nb + k, nb + k2, b + k2))
    fs.append((0, 3, 2, 1))
    e = 4 * seg
    fs.append((e, e + 1, e + 2, e + 3))
    ob = mesh_obj(name, vs, fs, mat)
    if bevel:
        add_bevel(ob, bevel, 3, 30)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.set_sharp_from_angle(angle=math.radians(40))
    return ob

def tapered_leg(name, x, y, h, r_top, r_bot, mat, splay=0.0):
    o = cylinder(name, r_top, h, (0, 0, 0), 16, mat, r2=r_bot)
    o.rotation_euler = (0, math.pi, 0)  # topo no z=0 -> inverter
    o.location = (x, y, h)
    if splay:
        o.rotation_euler = (math.copysign(splay, -y) + 0, math.pi + math.copysign(splay, x), 0)
    return o

# ================================================================ SALA
def sofa_curvo(name, M, loc, rot=0, R0=1.15, ang=110):
    """Sofá curvo em bouclé (planta mobiliar pág. 3 mostra sofá em arco)."""
    o = []
    a0 = math.radians(-90 - ang / 2); a1 = math.radians(-90 + ang / 2)
    # base de madeira recuada
    o.append(annulus(name + "_base", R0 + 0.05, R0 + 0.82, a0 + 0.03, a1 - 0.03, 0.0, 0.10, M["nogueira"], 64, 0.01))
    o.append(annulus(name + "_assento", R0, R0 + 0.82, a0, a1, 0.10, 0.44, M["boucle"], 64, 0.06))
    o.append(annulus(name + "_encosto", R0 + 0.68, R0 + 0.92, a0 - 0.02, a1 + 0.02, 0.10, 0.80, M["boucle"], 64, 0.09))
    # almofadas soltas
    for i, t in enumerate((0.18, 0.38, 0.62, 0.82)):
        a = a0 + (a1 - a0) * t
        rr = R0 + 0.62
        c = cushion(f"{name}_almofada{i}", 0.48, 0.16, 0.44, [M["linho"], M["veludo_oliva"], M["linho"], M["algodao_areia"]][i],
                    (rr * math.cos(a), rr * math.sin(a), 0.66))
        c.rotation_euler = (math.radians(-12), 0, a + math.pi / 2)
        o.append(c)
    # o centro do arco fica em loc; sofá ocupa o lado -Y (arco voltado p/ +Y após rot)
    return place(name, o, loc, rot)

def poltrona(name, M, loc, rot=0, mat=None):
    mat = mat or M["veludo_oliva"]
    o = []
    o.append(rb(name + "_assento", -0.36, 0.36, -0.36, 0.30, 0.20, 0.42, mat, 0.05))
    o.append(rb(name + "_encosto", -0.38, 0.38, 0.22, 0.40, 0.20, 0.82, mat, 0.07))
    o.append(rb(name + "_braco_e", -0.40, -0.28, -0.36, 0.40, 0.20, 0.60, mat, 0.05))
    o.append(rb(name + "_braco_d", 0.28, 0.40, -0.36, 0.40, 0.20, 0.60, mat, 0.05))
    o.append(cushion(name + "_almofada_assento", 0.54, 0.6, 0.12, mat, (0, -0.04, 0.46)))
    for x in (-0.33, 0.33):
        for y in (-0.31, 0.35):
            o.append(cylinder(f"{name}_pe{x}{y}", 0.018, 0.20, (x, y, 0), 12, M["nogueira"], r2=0.024))
    o.append(cushion(name + "_almofada", 0.42, 0.14, 0.32, M["linho"], (0.05, 0.18, 0.66)))
    o[-1].rotation_euler = (math.radians(-15), 0, math.radians(8))
    return place(name, o, loc, rot)

def mesa_centro(name, M, loc):
    o = [cylinder(name + "_tampo", 0.55, 0.05, (0, 0, 0.34), 64, M["travertino"]),
         cylinder(name + "_base", 0.38, 0.34, (0, 0, 0), 48, M["travertino"])]
    add_bevel(o[0], 0.008, 2)
    # objetos: livros + vaso + bandeja
    o.append(box(name + "_livro1", -0.25, 0.05, -0.12, 0.10, 0.39, 0.43, M["livro_b"], bevel=0.003))
    o.append(box(name + "_livro2", -0.22, 0.02, -0.10, 0.08, 0.43, 0.46, M["livro_a"], bevel=0.003))
    o.append(cylinder(name + "_vaso", 0.07, 0.22, (0.22, 0.05, 0.39), 32, M["ceramica_terracota"], r2=0.05))
    o.append(cylinder(name + "_bandeja", 0.16, 0.015, (0.05, -0.28, 0.39), 32, M["latao"]))
    o.append(sphere(name + "_vela", 0.045, (0.05, -0.28, 0.45), 16, 8, M["ceramica_off"], scale=(1, 1, 1.3)))
    return place(name, o, loc)

def mesa_lateral(name, M, loc, h=0.55):
    o = [cylinder(name + "_tampo", 0.24, 0.03, (0, 0, h - 0.03), 48, M["nogueira"]),
         cylinder(name + "_haste", 0.03, h - 0.03, (0, 0, 0.02), 16, M["latao"]),
         cylinder(name + "_base", 0.17, 0.02, (0, 0, 0), 48, M["latao"])]
    return place(name, o, loc)

def tapete(name, w, d, M, mat, loc, rot=0):
    o = [box(name, -w / 2, w / 2, -d / 2, d / 2, 0.001, 0.014, mat, bevel=0.006, seg=2)]
    return place(name, o, loc, rot)

def rack_tv(name, M, loc, rot=0, w=3.2):
    """Painel ripado de carvalho + rack suspenso + TV 65"."""
    o = []
    # painel ripado (ripas 4 cm, junta 1,5 cm) até a sanca
    n = int(w / 0.055)
    for i in range(n):
        x = -w / 2 + i * 0.055
        o.append(box(f"{name}_ripa{i}", x, x + 0.04, 0.0, 0.025, 0.0, 2.93, M["carvalho"]))
    o.append(box(name + "_fundo_ripado", -w / 2, w / 2, 0.025, 0.035, 0.0, 2.93, M["nogueira"]))
    # rack suspenso
    o.append(rb(name + "_rack", -1.20, 1.20, -0.45, 0.0, 0.25, 0.60, M["nogueira"], 0.008))
    for i in range(4):
        x = -1.20 + 0.6 * i
        o.append(box(f"{name}_frente{i}", x + 0.005, x + 0.595, -0.456, -0.45, 0.26, 0.59, M["nogueira"]))
    o.append(box(name + "_tampo_pedra", -1.21, 1.21, -0.46, 0.0, 0.60, 0.62, M["travertino"], bevel=0.003))
    # TV 65"
    o.append(box(name + "_tv", -0.72, 0.72, -0.06, -0.03, 1.05, 1.88, M["alu_preto"], bevel=0.004))
    o.append(box(name + "_tela", -0.71, 0.71, -0.061, -0.059, 1.06, 1.87, M["tela_tv"]))
    # objetos sobre o rack
    o.append(cylinder(name + "_vaso1", 0.09, 0.32, (-0.9, -0.22, 0.62), 32, M["ceramica_off"], r2=0.05))
    o.append(cylinder(name + "_vaso2", 0.06, 0.20, (-0.72, -0.25, 0.62), 32, M["ceramica_terracota"], r2=0.07))
    for k in range(3):
        o.append(box(f"{name}_livro{k}", 0.65, 0.95, -0.33, -0.12, 0.62 + k * 0.035, 0.655 + k * 0.035, [M["livro_a"], M["livro_b"], M["livro_c"]][k], bevel=0.002))
    o.append(sphere(name + "_obj", 0.07, (0.8, -0.22, 0.80), 24, 12, M["ceramica_terracota"]))
    # fita LED atrás da TV (rasante no ripado)
    o.append(box(name + "_led", -0.6, 0.6, -0.025, -0.02, 1.90, 1.905, M["led"]))
    return place(name, o, loc, rot)

def aparador(name, M, loc, rot=0, w=1.6, d=0.40, h=0.80, mat=None):
    mat = mat or M["nogueira"]
    o = [rb(name + "_corpo", -w / 2, w / 2, -d / 2, d / 2, 0.12, h, mat, 0.006)]
    for i in range(4):
        x = -w / 2 + w * i / 4
        o.append(box(f"{name}_porta{i}", x + 0.004, x + w / 4 - 0.004, -d / 2 - 0.004, -d / 2, 0.135, h - 0.015, mat))
        o.append(box(f"{name}_puxador{i}", x + w / 8 - 0.04, x + w / 8 + 0.04, -d / 2 - 0.02, -d / 2 - 0.004, h - 0.10, h - 0.09, M["latao"]))
    for x in (-w / 2 + 0.06, w / 2 - 0.06):
        for y in (-d / 2 + 0.06, d / 2 - 0.06):
            o.append(cylinder(f"{name}_pe{x}{y}", 0.015, 0.12, (x, y, 0), 12, M["latao"]))
    return place(name, o, loc, rot)

def quadro(name, M, art, w, h, loc, rot=0, frame=None, depth=0.03):
    """Quadro com moldura e passe-partout; imagem com UV 0..1."""
    frame = frame or M["nogueira"]
    o = []
    f = 0.03
    o.append(box(name + "_mold_s", -w / 2, w / 2, 0, depth, h / 2 - f, h / 2, frame))
    o.append(box(name + "_mold_i", -w / 2, w / 2, 0, depth, -h / 2, -h / 2 + f, frame))
    o.append(box(name + "_mold_e", -w / 2, -w / 2 + f, 0, depth, -h / 2, h / 2, frame))
    o.append(box(name + "_mold_d", w / 2 - f, w / 2, 0, depth, -h / 2, h / 2, frame))
    o.append(box(name + "_passe", -w / 2 + f, w / 2 - f, 0.01, depth, -h / 2 + f, h / 2 - f, M["linho_branco"]))
    m = 0.07
    v = [(-w / 2 + f + m, 0.009, -h / 2 + f + m), (w / 2 - f - m, 0.009, -h / 2 + f + m),
         (w / 2 - f - m, 0.009, h / 2 - f - m), (-w / 2 + f + m, 0.009, h / 2 - f - m)]
    pic = mesh_obj(name + "_gravura", v, [(0, 3, 2, 1)], M[art])
    uv = pic.data.uv_layers.new(name="UVMap")
    for li, lv in enumerate(pic.data.polygons[0].vertices):
        co = v[lv]
        uv.data[li].uv = ((co[0] + w / 2) / w, (co[2] + h / 2) / h)
    pic["keep_uv"] = 1
    o.append(pic)
    return place(name, o, loc, rot)

def foliage(name, M, clusters, leaf_len, leaf_w, per_cluster, radius, seed, mat=None, droop=0.35, branch_mat=None, base=None):
    """Folhagem presa a ramos: cada cluster (ponta de galho) recebe folhas em torno dele,
    e um galho fino liga a base ao cluster. Devolve [malha_folhas, malha_galhos]."""
    rr = random.Random(seed)
    verts, faces, uvs = [], [], []
    bv, bf = [], []
    for ci, c in enumerate(clusters):
        c = Vector(c)
        if base is not None:
            b0 = Vector(base); k = len(bv)
            mid = (b0 + c) / 2 + Vector((0, 0, 0.08))
            w = 0.012
            for p in (b0, mid, c):
                bv += [p + Vector((-w, 0, 0)), p + Vector((w, 0, 0)), p + Vector((0, w, 0))]
            for s_ in range(2):
                for t_ in range(3):
                    a0 = k + s_ * 3 + t_; a1 = k + s_ * 3 + (t_ + 1) % 3
                    bf.append((a0, a1, a1 + 3, a0 + 3))
        for i in range(per_cluster):
            u = Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, 0.7))).normalized()
            p = c + u * radius * (rr.random() ** 0.6)
            d = (p - c).normalized() if (p - c).length > 1e-4 else Vector((1, 0, 0))
            d = Vector((d.x, d.y, d.z - droop)).normalized()
            t = d.cross(Vector((rr.uniform(-.3, .3), rr.uniform(-.3, .3), 1))).normalized()
            L2 = leaf_len * rr.uniform(0.7, 1.25); W2 = leaf_w * rr.uniform(0.75, 1.2)
            p0 = p - t * W2 / 2; p1 = p + t * W2 / 2
            k = len(verts)
            verts += [p0, p1, p1 + d * L2, p0 + d * L2]
            faces.append((k, k + 1, k + 2, k + 3))
            cell = rr.randrange(16); cx, cy = cell % 4, cell // 4
            u0, v0 = cx / 4, 1 - (cy + 1) / 4
            uvs += [(u0 + 0.25, v0), (u0 + 0.25, v0 + 0.25), (u0, v0 + 0.25), (u0, v0)]
    lf = mesh_obj(name + "_folhas", verts, faces, mat or M["folha"])
    uvl = lf.data.uv_layers.new(name="UVMap")
    for li in range(len(uvl.data)):
        uvl.data[li].uv = uvs[li]
    lf["keep_uv"] = 1
    out = [lf]
    if bv:
        out.append(mesh_obj(name + "_galhos", bv, bf, branch_mat or M["tronco"]))
    return out

def palm_fronds(name, M, base, n=12, length=1.1, seed=1, rise=0.6):
    """Folhas de palmeira (areca): nervura curva + folíolos estreitos dos dois lados."""
    rr = random.Random(seed)
    verts, faces, uvs = [], [], []
    rv, rf = [], []
    base = Vector(base)
    for fi in range(n):
        az = 2 * math.pi * fi / n + rr.uniform(-0.25, 0.25)
        el = rr.uniform(0.75, 1.25)
        L = length * rr.uniform(0.75, 1.15)
        dirh = Vector((math.cos(az), math.sin(az), 0))
        pts = []
        for k in range(13):
            t = k / 12
            hz = math.sin(el) * L * t - (t ** 2) * L * 0.55
            hp = math.cos(el) * L * t + t * L * 0.25
            pts.append(base + dirh * hp + Vector((0, 0, hz + rise * t * 0.2)))
        k0 = len(rv)
        for p in pts:
            rv += [p, p + Vector((0, 0, 0.012))]
        for k in range(12):
            a = k0 + 2 * k
            rf.append((a, a + 2, a + 3, a + 1))
        side = dirh.cross(Vector((0, 0, 1))).normalized()
        for k in range(2, 13):
            p = pts[k]
            fwd = (pts[min(k + 1, 12)] - pts[k - 1]).normalized()
            ll = 0.32 * (1 - abs(k / 12 - 0.45)) + 0.08
            for sgn in (-1, 1):
                d = (side * sgn * 0.85 + fwd * 0.45 + Vector((0, 0, -0.25))).normalized()
                w = 0.035
                t = fwd
                q0 = p - t * w / 2; q1 = p + t * w / 2
                kk = len(verts)
                verts += [q0, q1, q1 + d * ll, q0 + d * ll]
                faces.append((kk, kk + 1, kk + 2, kk + 3))
                uvs += [(0.6, 0.0), (0.65, 0.0), (0.65, 0.25), (0.6, 0.25)]
    lf = mesh_obj(name + "_foliolos", verts, faces, M["folha"])
    uvl = lf.data.uv_layers.new(name="UVMap")
    for li in range(len(uvl.data)):
        uvl.data[li].uv = uvs[li]
    lf["keep_uv"] = 1
    return [lf, mesh_obj(name + "_nervuras", rv, rf, M["tronco"])]

def planta_vaso(name, M, loc, h=1.6, pot_r=0.22, kind="ficus", pot=None, leaves=140, seed=1):
    """Planta em vaso. kind: ficus | oliveira | palmeira."""
    rr = random.Random(seed)
    pot = pot or M["ceramica_terracota"]
    top = pot_r * 1.6
    o = [cylinder(name + "_vaso", pot_r, top, (0, 0, 0), 40, pot, r2=pot_r * 1.12),
         cylinder(name + "_terra", pot_r * 1.05, 0.02, (0, 0, top - 0.04), 32, M["terra"])]
    if kind == "palmeira":
        stems = 3
        for s_ in range(stems):
            off = Vector((rr.uniform(-.06, .06), rr.uniform(-.06, .06), 0))
            sh = h * rr.uniform(0.35, 0.5)
            o.append(cylinder(f"{name}_estipe{s_}", 0.02, sh, (off.x, off.y, top - 0.02), 10, M["veludo_oliva"], r2=0.014))
            o += palm_fronds(f"{name}_p{s_}", M, (off.x, off.y, top + sh), n=6, length=h * 0.55, seed=seed * 10 + s_)
    else:
        trunk_h = h * (0.55 if kind == "ficus" else 0.5)
        o.append(cylinder(name + "_tronco", 0.03, trunk_h, (0, 0, top - 0.02), 10, M["tronco"], r2=0.018))
        nb = 7 if kind == "ficus" else 10
        clusters = []
        for b_ in range(nb):
            a = 2 * math.pi * b_ / nb + rr.uniform(-0.3, 0.3)
            rad = h * (0.16 if kind == "ficus" else 0.22) * rr.uniform(0.6, 1.0)
            z = top + trunk_h + h * rr.uniform(-0.12, 0.35)
            clusters.append((rad * math.cos(a), rad * math.sin(a), z))
        if kind == "ficus":
            o += foliage(name, M, clusters, 0.24, 0.17, max(8, leaves // nb), 0.20, seed, droop=0.5, base=(0, 0, top + trunk_h * 0.85))
        else:
            o += foliage(name, M, clusters, 0.075, 0.022, max(20, leaves // nb), 0.22, seed, droop=0.1, base=(0, 0, top + trunk_h * 0.9))
    return place(name, o, loc, nota="Vegetação: proposta")

# ================================================================ JANTAR / COZINHA
def mesa_jantar(name, M, loc, rot=0, L=2.40, W=1.00):
    o = [rb(name + "_tampo", -W / 2, W / 2, -L / 2, L / 2, 0.72, 0.76, M["carvalho"], 0.006)]
    # base em dois cavaletes de madeira maciça
    for y in (-L / 2 + 0.35, L / 2 - 0.35):
        o.append(rb(f"{name}_cav{y}", -W / 2 + 0.12, W / 2 - 0.12, y - 0.04, y + 0.04, 0.0, 0.05, M["nogueira"], 0.01))
        o.append(rb(f"{name}_col{y}", -0.05, 0.05, y - 0.04, y + 0.04, 0.05, 0.72, M["nogueira"], 0.01))
        o.append(rb(f"{name}_trav{y}", -W / 2 + 0.12, W / 2 - 0.12, y - 0.04, y + 0.04, 0.66, 0.72, M["nogueira"], 0.01))
    o.append(rb(name + "_viga", -0.04, 0.04, -L / 2 + 0.35, L / 2 - 0.35, 0.40, 0.48, M["nogueira"], 0.01))
    # centro de mesa: fruteira de cerâmica + 3 velas
    o.append(cylinder(name + "_fruteira", 0.18, 0.08, (0, 0, 0.76), 40, M["ceramica_off"], r2=0.22))
    for k in range(5):
        o.append(sphere(f"{name}_fruta{k}", 0.04, (0.06 * math.cos(k * 1.3), 0.06 * math.sin(k * 1.3), 0.85), 12, 8,
                        M["ceramica_terracota"] if k % 2 else M["veludo_oliva"]))
    for k, y in enumerate((-0.55, 0.5, 0.65)):
        o.append(cylinder(f"{name}_castical{k}", 0.03, 0.06 + 0.04 * k, (0.05 * (k - 1), y, 0.76), 16, M["latao"]))
        o.append(cylinder(f"{name}_vela{k}", 0.012, 0.18, (0.05 * (k - 1), y, 0.82 + 0.04 * k), 12, M["ceramica_off"]))
    return place(name, o, loc, rot)

def cadeira_jantar(name, M, loc, rot=0, mat=None):
    """Cadeira estofada com braços curtos e pés de madeira (referência 2)."""
    mat = mat or M["la_grafite"]
    o = []
    o.append(rb(name + "_assento", -0.25, 0.25, -0.24, 0.22, 0.44, 0.50, mat, 0.03))
    o.append(rb(name + "_encosto", -0.27, 0.27, 0.16, 0.26, 0.46, 0.86, mat, 0.045))
    o.append(rb(name + "_braco_e", -0.29, -0.21, -0.12, 0.24, 0.50, 0.68, mat, 0.035))
    o.append(rb(name + "_braco_d", 0.21, 0.29, -0.12, 0.24, 0.50, 0.68, mat, 0.035))
    for x in (-0.21, 0.21):
        for y in (-0.19, 0.18):
            lg = cylinder(f"{name}_pe{x}{y}", 0.022, 0.45, (x, y, 0), 12, M["carvalho"], r2=0.014)
            lg.rotation_euler = (math.copysign(0.08, y), -math.copysign(0.06, x), 0)
            o.append(lg)
    return place(name, o, loc, rot)

def pendente_globos(name, M, loc, n=7, span=1.6, ceiling=3.05):
    """Luminária com globos de vidro em alturas variadas (referência 2)."""
    rr = random.Random(7)
    o = [rb(name + "_canopla", -span / 2 - 0.1, span / 2 + 0.1, -0.09, 0.09, ceiling - 0.03, ceiling, M["latao"], 0.004)]
    for i in range(n):
        x = -span / 2 + span * i / (n - 1) + rr.uniform(-0.05, 0.05)
        y = rr.uniform(-0.05, 0.05)
        r = rr.choice((0.09, 0.11, 0.14, 0.12))
        z = ceiling - rr.uniform(0.75, 1.15)
        o.append(cylinder(f"{name}_cabo{i}", 0.003, ceiling - z - r, (x, y, z + r), 6, M["alu_preto"]))
        o.append(sphere(f"{name}_globo{i}", r, (x, y, z), 32, 16, M["vidro_globo"]))
        o.append(cylinder(f"{name}_soquete{i}", 0.018, 0.04, (x, y, z + r - 0.02), 12, M["latao"]))
        b = sphere(f"{name}_lampada{i}", 0.022, (x, y, z), 12, 8, M["lampada"])
        b["luz"] = 1
        o.append(b)
    return place(name, o, loc, cat="iluminacao")

def ilha(name, M, x0, x1, y0, y1):
    """Ilha da cozinha (pág. 2: 1,10 x 3,35; pág. 3: cooktop ao norte, cuba ao sul;
    corte A/A: bancada 0,90 e balcão elevado 1,10 do lado da sala)."""
    o = []
    H = 0.90; top = 0.03
    # caixa de marcenaria
    o.append(box(name + "_corpo", x0 + 0.05, x1, y0, y1, 0.10, H - top, M["carvalho"]))
    o.append(box(name + "_rodape", x0 + 0.10, x1 - 0.05, y0 + 0.05, y1 - 0.05, 0.0, 0.10, M["nogueira"]))
    # frentes de gaveta/porta no lado leste (área de trabalho) com puxadores de latão
    n = int((y1 - y0) / 0.60)
    for i in range(n):
        ya = y0 + 0.02 + i * (y1 - y0 - 0.04) / n
        yb = ya + (y1 - y0 - 0.04) / n - 0.004
        for k, (za, zb) in enumerate(((0.12, 0.38), (0.39, 0.62), (0.63, 0.84))):
            o.append(box(f"{name}_frente{i}_{k}", x1, x1 + 0.006, ya, yb, za, zb, M["carvalho"]))
            o.append(box(f"{name}_pux{i}_{k}", x1 + 0.006, x1 + 0.02, (ya + yb) / 2 - 0.08, (ya + yb) / 2 + 0.08, zb - 0.05, zb - 0.04, M["latao"]))
    # tampo de quartzo com recorte para cuba (cuba ao sul) e cooktop (ao norte)
    sx0, sx1 = x0 + 0.30, x0 + 0.80   # cuba 0,50 x 0,40
    sy0, sy1 = y0 + 0.55, y0 + 0.95
    T = M["calacatta"]
    o.append(box(name + "_tampo_a", x0, x1 + 0.02, y0 - 0.02, sy0, H - top, H, T))
    o.append(box(name + "_tampo_b", x0, x1 + 0.02, sy1, y1 + 0.02, H - top, H, T))
    o.append(box(name + "_tampo_c", x0, sx0, sy0, sy1, H - top, H, T))
    o.append(box(name + "_tampo_d", sx1, x1 + 0.02, sy0, sy1, H - top, H, T))
    # cuba de inox com profundidade real (20 cm) — 5 faces voltadas para dentro
    d = 0.20; z1 = H - top; z0 = z1 - d
    v = [(sx0, sy0, z0), (sx1, sy0, z0), (sx1, sy1, z0), (sx0, sy1, z0),
         (sx0, sy0, z1), (sx1, sy0, z1), (sx1, sy1, z1), (sx0, sy1, z1)]
    f = [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    o.append(mesh_obj(name + "_cuba", v, f, M["inox"]))
    o.append(cylinder(name + "_ralo", 0.04, 0.003, ((sx0 + sx1) / 2, (sy0 + sy1) / 2, z0 + 0.001), 24, M["cromado"]))
    # misturador gourmet (latão) no lado leste da cuba
    fx = sx1 + 0.08; fy = (sy0 + sy1) / 2
    o.append(cylinder(name + "_torneira_base", 0.025, 0.05, (fx, fy, H), 24, M["latao"]))
    o.append(cylinder(name + "_torneira_corpo", 0.014, 0.30, (fx, fy, H + 0.05), 16, M["latao"]))
    arc = torus(name + "_torneira_bica", 0.12, 0.012, (fx - 0.12, fy, H + 0.35), 24, 8, M["latao"], arc=math.pi)
    arc.rotation_euler = (math.pi / 2, 0, 0); arc.location = (fx - 0.12, fy, H + 0.35)
    o.append(arc)
    o.append(box(name + "_torneira_alav", fx - 0.005, fx + 0.07, fy - 0.006, fy + 0.006, H + 0.24, H + 0.25, M["latao"]))
    # cooktop de indução (vidro preto embutido) ao norte
    cy0, cy1 = y1 - 0.95, y1 - 0.20
    o.append(box(name + "_cooktop", x0 + 0.40, x1 - 0.12, cy0, cy1, H, H + 0.006, M["vidro_preto"], bevel=0.003))
    for k, (cx, cyy, rr_) in enumerate(((x0 + 0.58, cy0 + 0.18, 0.10), (x0 + 0.58, cy1 - 0.20, 0.12), (x1 - 0.30, cy0 + 0.18, 0.08), (x1 - 0.30, cy1 - 0.20, 0.10))):
        o.append(torus(f"{name}_zona{k}", rr_, 0.002, (cx, cyy, H + 0.0065), 32, 4, M["inox"]))
    # balcão elevado (1,10) do lado oeste com sobra para os joelhos
    o.append(box(name + "_balcao", x0 - 0.30, x0 + 0.12, y0 + 0.20, y1 - 0.20, 1.07, 1.10, T))
    o.append(box(name + "_balcao_frente", x0 - 0.02, x0 + 0.05, y0, y1, 0.10, 1.07, M["carvalho"]))
    # objetos: tábua, fruteira, ervas
    o.append(box(name + "_tabua", x1 - 0.42, x1 - 0.12, y0 + 1.25, y0 + 1.70, H, H + 0.02, M["carvalho"], bevel=0.005))
    o.append(cylinder(name + "_pote", 0.06, 0.15, (x1 - 0.2, y0 + 1.85, H), 24, M["ceramica_off"]))
    o.append(cylinder(name + "_ervas", 0.05, 0.12, (x0 - 0.12, y0 + 1.6, 1.10), 24, M["ceramica_terracota"]))
    return o

def banqueta(name, M, loc, rot=0):
    o = [cylinder(name + "_assento", 0.20, 0.05, (0, 0, 0.72), 32, M["couro"]),
         torus(name + "_aro", 0.17, 0.008, (0, 0, 0.30), 32, 8, M["latao"])]
    add_bevel(o[0], 0.015, 3)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        lg = cylinder(f"{name}_pe{k}", 0.014, 0.74, (0.17 * math.cos(a), 0.17 * math.sin(a), 0), 10, M["nogueira"], r2=0.016)
        lg.rotation_euler = (-math.sin(a) * 0.08, math.cos(a) * 0.08, 0)
        o.append(lg)
    return place(name, o, loc, rot)

def coifa(name, M, x, y, zb=1.70, ceiling=3.05):
    """Coifa de ilha (corte A/A: base a 0,90+0,80 = 1,70)."""
    o = [rb(name + "_corpo", x - 0.45, x + 0.45, y - 0.30, y + 0.30, zb, zb + 0.12, M["inox"], 0.006),
         box(name + "_duto", x - 0.14, x + 0.14, y - 0.12, y + 0.12, zb + 0.12, ceiling, M["inox"]),
         box(name + "_filtro", x - 0.40, x + 0.40, y - 0.25, y + 0.25, zb - 0.002, zb, M["alu_preto"])]
    for k in (-0.2, 0.2):
        L = box(f"{name}_luz{k}", x + k - 0.03, x + k + 0.03, y - 0.03, y + 0.03, zb - 0.003, zb - 0.001, M["led_forte"])
        L["luz"] = 1
        o.append(L)
    return o

def torre_nicho(name, M, x0, x1, y0, y1, h=2.90):
    """Marcenaria do nicho 0,60 (pág. 3: armário alto + geladeira ao sul)."""
    o = []
    o.append(box(name + "_caixa", x0, x1, y0, y1, 0.0, h, M["carvalho"]))
    fx = x1  # frentes voltadas para leste? Não: o nicho abre para oeste (x0)
    n = 5
    w = (y1 - y0) / n
    for i in range(n):
        ya, yb = y0 + i * w + 0.003, y0 + (i + 1) * w - 0.003
        if i == 0:   # geladeira integrada (porta inteira)
            o.append(box(f"{name}_geladeira", x0 - 0.02, x0, ya, yb, 0.10, h - 0.003, M["carvalho"]))
            o.append(box(f"{name}_gel_pux", x0 - 0.05, x0 - 0.02, yb - 0.06, yb - 0.04, 0.9, 1.8, M["latao"]))
        elif i == 2:  # torre quente: forno + micro-ondas em vidro preto
            o.append(box(f"{name}_forno", x0 - 0.02, x0, ya, yb, 0.85, 1.45, M["vidro_preto"]))
            o.append(box(f"{name}_micro", x0 - 0.02, x0, ya, yb, 1.48, 1.86, M["vidro_preto"]))
            o.append(box(f"{name}_forno_pux", x0 - 0.04, x0 - 0.02, ya + 0.05, yb - 0.05, 1.38, 1.40, M["inox"]))
            o.append(box(f"{name}_inf", x0 - 0.02, x0, ya, yb, 0.10, 0.82, M["carvalho"]))
            o.append(box(f"{name}_sup", x0 - 0.02, x0, ya, yb, 1.89, h - 0.003, M["carvalho"]))
        else:
            o.append(box(f"{name}_porta{i}_inf", x0 - 0.02, x0, ya, yb, 0.10, 2.10, M["carvalho"]))
            o.append(box(f"{name}_porta{i}_sup", x0 - 0.02, x0, ya, yb, 2.113, h - 0.003, M["carvalho"]))
            o.append(box(f"{name}_pux{i}", x0 - 0.045, x0 - 0.02, yb - 0.05, yb - 0.035, 0.95, 1.55, M["latao"]))
    o.append(box(name + "_rodape", x0 - 0.02, x0 + 0.05, y0, y1, 0, 0.10, M["nogueira"]))
    return o

def cristaleira(name, M, loc, rot=0, w=1.8, d=0.40):
    """Aparador-cristaleira (base fechada + nichos abertos) na parede norte da cozinha."""
    o = [rb(name + "_base", -w / 2, w / 2, -d / 2, d / 2, 0.10, 0.88, M["carvalho"], 0.004),
         box(name + "_tampo", -w / 2 - 0.01, w / 2 + 0.01, -d / 2 - 0.02, d / 2, 0.88, 0.91, M["calacatta"], bevel=0.002),
         box(name + "_rodape", -w / 2 + 0.03, w / 2 - 0.03, -d / 2 + 0.03, d / 2, 0.0, 0.10, M["nogueira"])]
    for i in range(3):
        x = -w / 2 + w * i / 3
        o.append(box(f"{name}_porta{i}", x + 0.004, x + w / 3 - 0.004, -d / 2 - 0.006, -d / 2, 0.12, 0.86, M["carvalho"]))
        o.append(box(f"{name}_pux{i}", x + w / 6 - 0.06, x + w / 6 + 0.06, -d / 2 - 0.02, -d / 2 - 0.006, 0.80, 0.81, M["latao"]))
    # nichos abertos superiores (prateleiras com louças)
    for k, z in enumerate((1.45, 1.85, 2.25)):
        o.append(box(f"{name}_prat{k}", -w / 2, w / 2, -0.12, d / 2 - 0.12, z, z + 0.03, M["carvalho"]))
        for j in range(5):
            x = -w / 2 + 0.2 + j * (w - 0.4) / 4
            kind = (j + k) % 3
            if kind == 0:
                o.append(cylinder(f"{name}_pote{k}{j}", 0.07, 0.18, (x, 0.0, z + 0.03), 24, M["ceramica_off"], r2=0.05))
            elif kind == 1:
                for p in range(4):
                    o.append(cylinder(f"{name}_prato{k}{j}{p}", 0.11, 0.012, (x, 0.0, z + 0.03 + p * 0.014), 32, M["ceramica_off"], r2=0.12))
            else:
                o.append(sphere(f"{name}_jarro{k}{j}", 0.08, (x, 0.0, z + 0.11), 24, 12, M["ceramica_terracota"], scale=(1, 1, 1.2)))
    return place(name, o, loc, rot)

# ================================================================ QUARTOS
def cama(name, M, loc, rot=0, W=1.80, L=2.05, cab_h=1.25, cab_mat=None, duvet=None, throw=None, solteiro=False):
    cab_mat = cab_mat or M["linho"]
    duvet = duvet or M["linho_branco"]
    o = []
    # cabeceira estofada (no +Y local) e base
    o.append(rb(name + "_cabeceira", -W / 2 - 0.05, W / 2 + 0.05, L / 2 - 0.10, L / 2, 0.0, cab_h, cab_mat, 0.04, 4))
    if not solteiro:
        for k in range(4):
            x = -W / 2 + (k + 0.5) * W / 4
            o.append(rb(f"{name}_gomo{k}", x - W / 8 + 0.01, x + W / 8 - 0.01, L / 2 - 0.13, L / 2 - 0.09, 0.55, cab_h - 0.06, cab_mat, 0.03, 4))
    o.append(rb(name + "_base", -W / 2, W / 2, -L / 2, L / 2 - 0.10, 0.10, 0.36, cab_mat, 0.03))
    o.append(box(name + "_rodape", -W / 2 + 0.05, W / 2 - 0.05, -L / 2 + 0.05, L / 2 - 0.15, 0.0, 0.10, M["nogueira"]))
    o.append(rb(name + "_colchao", -W / 2 + 0.02, W / 2 - 0.02, -L / 2 + 0.02, L / 2 - 0.12, 0.36, 0.60, M["linho_branco"], 0.05, 3))
    # edredom caindo nas laterais
    o.append(rb(name + "_edredom", -W / 2 - 0.04, W / 2 + 0.04, -L / 2 - 0.03, L / 2 - 0.55, 0.42, 0.65, duvet, 0.05, 4))
    o.append(rb(name + "_dobra", -W / 2 - 0.045, W / 2 + 0.045, L / 2 - 0.85, L / 2 - 0.55, 0.42, 0.67, M["linho_branco"], 0.05, 4))
    if throw:
        o.append(rb(name + "_peseira", -W / 2 - 0.05, W / 2 + 0.05, -L / 2 + 0.15, -L / 2 + 0.70, 0.43, 0.675, throw, 0.03, 3))
    # travesseiros
    np_ = 1 if solteiro else 2
    for k in range(np_):
        x = 0 if solteiro else (-W / 4 + k * W / 2)
        pw = W - 0.25 if solteiro else W / 2 - 0.08
        c = cushion(f"{name}_travesseiro{k}", pw, 0.42, 0.16, M["linho_branco"], (x, L / 2 - 0.40, 0.68))
        c.rotation_euler = (math.radians(-65), 0, 0)
        o.append(c)
        c2 = cushion(f"{name}_almofada{k}", pw - 0.12, 0.14, 0.38, cab_mat if not solteiro else M["linho_rosa"], (x, L / 2 - 0.55, 0.78))
        c2.rotation_euler = (math.radians(-18), 0, 0)
        o.append(c2)
    if not solteiro:
        c3 = cushion(name + "_almofada_rolo", 0.55, 0.16, 0.16, M["veludo_oliva"], (0, L / 2 - 0.72, 0.72))
        o.append(c3)
    return place(name, o, loc, rot)

def criado(name, M, loc, rot=0, w=0.50, d=0.40, h=0.55, lamp=True, mat=None):
    mat = mat or M["nogueira"]
    o = [rb(name + "_corpo", -w / 2, w / 2, -d / 2, d / 2, 0.15, h, mat, 0.006)]
    o.append(box(name + "_gaveta", -w / 2 + 0.01, w / 2 - 0.01, -d / 2 - 0.004, -d / 2, h - 0.17, h - 0.02, mat))
    o.append(box(name + "_pux", -0.05, 0.05, -d / 2 - 0.018, -d / 2 - 0.004, h - 0.10, h - 0.09, M["latao"]))
    for x in (-w / 2 + 0.04, w / 2 - 0.04):
        for y in (-d / 2 + 0.04, d / 2 - 0.04):
            o.append(cylinder(f"{name}_pe{x}{y}", 0.012, 0.15, (x, y, 0), 10, M["latao"]))
    if lamp:
        o.append(sphere(name + "_abajur_base", 0.09, (0, 0.03, h + 0.11), 24, 12, M["ceramica_off"], scale=(1, 1, 1.2)))
        o.append(cylinder(name + "_abajur_haste", 0.008, 0.12, (0, 0.03, h + 0.21), 8, M["latao"]))
        sh = cylinder(name + "_cupula", 0.16, 0.22, (0, 0.03, h + 0.30), 40, M["linho_branco"], r2=0.12, cap=False)
        o.append(sh)
        b = sphere(name + "_lampada", 0.03, (0, 0.03, h + 0.40), 12, 8, M["lampada"]); b["luz"] = 1
        o.append(b)
    o.append(box(name + "_livro", -0.15, 0.05, -0.12, 0.05, h, h + 0.03, M["livro_c"], bevel=0.002))
    return place(name, o, loc, rot)

def guarda_roupa(name, M, x0, x1, y0, y1, h=2.90, front="-y", mat=None, nportas=None):
    """Armário embutido até o forro, portas de giro com frisos e puxadores de latão."""
    mat = mat or M["carvalho"]
    o = [box(name + "_caixa", x0, x1, y0, y1, 0.0, h, mat)]
    along_x = front in ("-y", "+y")
    a0, a1 = (x0, x1) if along_x else (y0, y1)
    n = nportas or max(2, int(round((a1 - a0) / 0.48)))
    w = (a1 - a0) / n
    for i in range(n):
        a, b = a0 + i * w + 0.002, a0 + (i + 1) * w - 0.002
        for (za, zb) in (((0.10, 2.25), (2.255, h - 0.003)) if h > 2.4 else ((0.10, h - 0.003),)):
            if front == "-y":
                o.append(box(f"{name}_p{i}_{za}", a, b, y0 - 0.02, y0, za, zb, mat))
            elif front == "+y":
                o.append(box(f"{name}_p{i}_{za}", a, b, y1, y1 + 0.02, za, zb, mat))
            elif front == "-x":
                o.append(box(f"{name}_p{i}_{za}", x0 - 0.02, x0, a, b, za, zb, mat))
            else:
                o.append(box(f"{name}_p{i}_{za}", x1, x1 + 0.02, a, b, za, zb, mat))
        # puxador vertical alternado
        hx = b - 0.04 if i % 2 == 0 else a + 0.04
        if front == "-y":
            o.append(box(f"{name}_pux{i}", hx - 0.006, hx + 0.006, y0 - 0.045, y0 - 0.02, 0.95, 1.45, M["latao"]))
        elif front == "+y":
            o.append(box(f"{name}_pux{i}", hx - 0.006, hx + 0.006, y1 + 0.02, y1 + 0.045, 0.95, 1.45, M["latao"]))
        elif front == "-x":
            o.append(box(f"{name}_pux{i}", x0 - 0.045, x0 - 0.02, hx - 0.006, hx + 0.006, 0.95, 1.45, M["latao"]))
        else:
            o.append(box(f"{name}_pux{i}", x1 + 0.02, x1 + 0.045, hx - 0.006, hx + 0.006, 0.95, 1.45, M["latao"]))
    if front == "-y":
        o.append(box(name + "_rodape", x0, x1, y0 - 0.02, y0 + 0.05, 0, 0.10, M["nogueira"]))
    return o

def painel_treliça(name, M, x, y0, y1, z0, z1, cell=0.085, depth=0.06, mat=None):
    """Painel em treliça de madeira com LED de contorno (referência do quarto rosé)."""
    mat = mat or M["carvalho"]
    o = []
    t = 0.018
    ny = int((y1 - y0) / cell)
    nz = int((z1 - z0) / cell)
    for i in range(ny + 1):
        yy = y0 + i * (y1 - y0) / ny
        o.append(box(f"{name}_v{i}", x, x + depth, yy - t / 2, yy + t / 2, z0, z1, mat))
    for k in range(nz + 1):
        zz = z0 + k * (z1 - z0) / nz
        o.append(box(f"{name}_h{k}", x, x + depth * 0.6, y0, y1, zz - t / 2, zz + t / 2, mat))
    o.append(box(name + "_fundo", x - 0.004, x, y0, y1, z0, z1, M["nogueira"]))
    led = box(name + "_led", x + 0.02, x + 0.03, y0 - 0.02, y1 + 0.02, z1 + 0.01, z1 + 0.02, M["led_forte"])
    led["luz"] = 1
    o.append(led)
    return o

def espelho_arco(name, M, loc, rot=0, w=0.80, h=1.60):
    """Penteadeira com espelho em arco moldurado em latão + LED (referência do quarto)."""
    o = []
    r = w / 2
    def arch_mesh(nm, inset, y0, y1, mat):
        """Contorno em arco (lados retos + semicírculo) com recuo 'inset'."""
        rr = r - inset
        pp = [(rr, inset)]
        for i in range(33):
            a = math.pi * i / 32
            pp.append((rr * math.cos(a), (h - r) + rr * math.sin(a)))
        pp.append((-rr, inset))
        n = len(pp)
        v = [(px, y0, pz) for px, pz in pp] + [(px, y1, pz) for px, pz in pp]
        f = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
        for i in range(n):
            j = (i + 1) % n
            f.append((i, n + i, n + j, j))
        return mesh_obj(nm, v, f, mat)
    o.append(arch_mesh(name + "_moldura", 0.0, 0.0, 0.025, M["latao"]))
    o.append(arch_mesh(name + "_espelho", 0.025, -0.003, 0.0, M["espelho"]))
    led = arch_mesh(name + "_led", -0.03, 0.026, 0.03, M["led"])
    led["luz"] = 1
    o.append(led)
    for ob in o:
        ob.location.z = 0.80
    # tampo da penteadeira
    o.append(rb(name + "_tampo", -0.60, 0.60, -0.48, 0.0, 0.72, 0.76, M["carvalho"], 0.005))
    o.append(box(name + "_gaveta", -0.58, 0.58, -0.485, -0.47, 0.62, 0.72, M["carvalho"]))
    for x in (-0.56, 0.56):
        o.append(box(f"{name}_pe{x}", x - 0.02, x + 0.02, -0.46, -0.02, 0.0, 0.62, M["carvalho"]))
    o.append(cylinder(name + "_vasinho", 0.04, 0.10, (0.35, -0.2, 0.76), 24, M["ceramica_off"]))
    o.append(box(name + "_caixa", -0.4, -0.2, -0.3, -0.15, 0.76, 0.82, M["palha"], bevel=0.005))
    return place(name, o, loc, rot)

def cadeira_boucle(name, M, loc, rot=0):
    o = [rb(name + "_assento", -0.24, 0.24, -0.22, 0.22, 0.44, 0.52, M["boucle"], 0.04, 4),
         annulus(name + "_encosto", 0.20, 0.26, math.radians(20), math.radians(160), 0.52, 0.80, M["boucle"], 24, 0.025)]
    o[1].location.y = -0.02
    for x in (-0.2, 0.2):
        for y in (-0.18, 0.18):
            o.append(cylinder(f"{name}_pe{x}{y}", 0.01, 0.44, (x, y, 0), 8, M["ferro"]))
    return place(name, o, loc, rot)

def pendente_globo(name, M, x, y, z, r=0.15, ceiling=3.05):
    o = [cylinder(name + "_cabo", 0.003, ceiling - z - r, (x, y, z + r), 6, M["alu_preto"]),
         sphere(name + "_globo", r, (x, y, z), 32, 16, M["opalina"]),
         cylinder(name + "_canopla", 0.05, 0.015, (x, y, ceiling - 0.015), 24, M["latao"])]
    b = sphere(name + "_lampada", 0.03, (x, y, z), 12, 8, M["lampada"]); b["luz"] = 1
    o.append(b)
    return o

def banco_peseira(name, M, loc, rot=0, w=1.4):
    o = [rb(name + "_assento", -w / 2, w / 2, -0.20, 0.20, 0.38, 0.48, M["veludo_oliva"], 0.03, 3)]
    for x in (-w / 2 + 0.05, w / 2 - 0.05):
        for y in (-0.15, 0.15):
            o.append(cylinder(f"{name}_pe{x}{y}", 0.015, 0.38, (x, y, 0), 10, M["latao"]))
    return place(name, o, loc, rot)

# ================================================================ BANHEIROS
def bacia(name, M, loc, rot=0):
    """Bacia com caixa acoplada (frente para -Y local, encosta na parede em +Y)."""
    o = [sphere(name + "_bacia", 0.19, (0, -0.06, 0.22), 32, 16, M["porcelana"], scale=(0.95, 1.3, 1.0)),
         rb(name + "_pe", -0.13, 0.13, -0.15, 0.10, 0.0, 0.25, M["porcelana"], 0.05),
         rb(name + "_caixa", -0.19, 0.19, 0.10, 0.28, 0.38, 0.78, M["porcelana"], 0.03),
         rb(name + "_assento", -0.18, 0.18, -0.30, 0.08, 0.40, 0.43, M["porcelana"], 0.03),
         cylinder(name + "_botao", 0.02, 0.01, (0, 0.19, 0.78), 16, M["cromado"])]
    # corta a metade de cima da esfera (bacia aberta) com bisect
    bm = bmesh.new(); bm.from_mesh(o[0].data)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0.36), plane_no=(0, 0, 1), clear_outer=True)
    bm.to_mesh(o[0].data); bm.free()
    sol = o[0].modifiers.new("Espessura", "SOLIDIFY"); sol.thickness = 0.015
    return place(name, o, loc, rot)

def bancada_banho(name, M, loc, rot=0, w=0.90, d=0.48, cubas=1, mat=None, top=None):
    """Gabinete suspenso + tampo com cuba de semi-encaixe esculpida (profundidade real)."""
    mat = mat or M["carvalho"]
    top = top or M["travertino"]
    o = [rb(name + "_gabinete", -w / 2, w / 2, -d / 2, d / 2, 0.30, 0.82, mat, 0.004)]
    for k in range(2):
        x0 = -w / 2 + k * w / 2
        o.append(box(f"{name}_porta{k}", x0 + 0.003, x0 + w / 2 - 0.003, -d / 2 - 0.006, -d / 2, 0.31, 0.81, mat))
        o.append(box(f"{name}_pux{k}", x0 + w / 4 - 0.05, x0 + w / 4 + 0.05, -d / 2 - 0.02, -d / 2 - 0.006, 0.77, 0.78, M["latao"]))
    T0 = 0.82; T1 = 0.85
    # tampo com recortes para cubas (de embutir, 0,40 x 0,30 x 0,14)
    xs = [0.0] if cubas == 1 else [-w / 4, w / 4]
    cw, cd, ch = 0.40, 0.30, 0.14
    if cubas == 1:
        cuts = [(-cw / 2, cw / 2)]
    else:
        cuts = [(x - cw / 2, x + cw / 2) for x in xs]
    yA, yB = -cd / 2 - 0.03, cd / 2 - 0.03
    o.append(box(name + "_tampo_f", -w / 2 - 0.01, w / 2 + 0.01, -d / 2 - 0.02, yA, T0, T1, top))
    o.append(box(name + "_tampo_t", -w / 2 - 0.01, w / 2 + 0.01, yB, d / 2, T0, T1, top))
    edges = [-w / 2 - 0.01] + [v for c in cuts for v in c] + [w / 2 + 0.01]
    for i in range(0, len(edges), 2):
        a, b = edges[i], edges[i + 1]
        if b - a > 0.001:
            o.append(box(f"{name}_tampo_m{i}", a, b, yA, yB, T0, T1, top))
    o.append(box(name + "_espelho_pedra", -w / 2 - 0.01, w / 2 + 0.01, d / 2 - 0.02, d / 2, T1, T1 + 0.10, top))
    for k, (a, b) in enumerate(cuts):
        z1 = T1; z0 = T1 - ch
        v = [(a, yA, z0), (b, yA, z0), (b, yB, z0), (a, yB, z0), (a, yA, z1), (b, yA, z1), (b, yB, z1), (a, yB, z1)]
        f = [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        cb = mesh_obj(f"{name}_cuba{k}", v, f, M["porcelana"])
        add_bevel(cb, 0.03, 3, 60)
        o.append(cb)
        cx = (a + b) / 2
        o.append(cylinder(f"{name}_ralo{k}", 0.022, 0.003, (cx, (yA + yB) / 2, z0 + 0.001), 16, M["latao"]))
        # misturador de parede/bica alta
        o.append(cylinder(f"{name}_mist{k}", 0.018, 0.22, (cx, yB + 0.06, T1), 16, M["latao"]))
        sp = cylinder(f"{name}_bica{k}", 0.010, 0.16, (cx, yB + 0.06, T1 + 0.21), 12, M["latao"], axis="Y")
        sp.rotation_euler = (math.radians(90), 0, 0); sp.location = (cx, yB + 0.06, T1 + 0.21)
        o.append(sp)
    # toalha e sabonete
    o.append(rb(name + "_toalha", w / 2 - 0.25, w / 2 - 0.05, -0.15, 0.05, T1, T1 + 0.06, M["linho_branco"], 0.02))
    o.append(cylinder(name + "_sabonete", 0.03, 0.12, (-w / 2 + 0.1, 0.1, T1), 16, M["ceramica_terracota"]))
    return place(name, o, loc, rot)

def espelho_banho(name, M, loc, rot=0, w=0.80, h=0.95, redondo=False):
    if redondo:
        o = [cylinder(name + "_moldura", w / 2, 0.02, (0, 0, 0), 64, M["latao"], axis="Y"),
             cylinder(name + "_espelho", w / 2 - 0.02, 0.003, (0, -0.003, 0), 64, M["espelho"], axis="Y")]
    else:
        o = [box(name + "_moldura", -w / 2, w / 2, 0, 0.025, -h / 2, h / 2, M["latao"], bevel=0.004),
             box(name + "_espelho", -w / 2 + 0.02, w / 2 - 0.02, -0.003, 0.0, -h / 2 + 0.02, h / 2 - 0.02, M["espelho"])]
        led = box(name + "_led", -w / 2 + 0.03, w / 2 - 0.03, 0.026, 0.03, h / 2 - 0.02, h / 2, M["led"]); led["luz"] = 1
        o.append(led)
    return place(name, o, loc, rot)

def box_chuveiro(name, M, x0, x1, y_glass, y_wall, door_side="x0", h=2.00):
    """Box de vidro temperado (fixo + porta) com perfil latão, chuveiro e nicho."""
    o = []
    t = 0.008
    w = x1 - x0
    split = x0 + w * 0.5
    o.append(box(name + "_fixo", split, x1, y_glass - t / 2, y_glass + t / 2, 0.02, h, M["vidro_box"]))
    o.append(box(name + "_porta", x0 + 0.02, split - 0.005, y_glass - t / 2 - 0.015, y_glass + t / 2 - 0.015, 0.02, h, M["vidro_box"]))
    o.append(box(name + "_perfil_sup", x0, x1, y_glass - 0.012, y_glass + 0.012, h, h + 0.02, M["latao"]))
    o.append(box(name + "_puxador", split - 0.06, split - 0.045, y_glass - 0.06, y_glass - 0.02, 0.9, 1.3, M["latao"]))
    # soleira/caimento e ralo linear
    o.append(box(name + "_ralo", x0 + 0.05, x1 - 0.05, y_wall - 0.10 if y_wall < y_glass else y_wall + 0.05,
                 y_wall - 0.05 if y_wall < y_glass else y_wall + 0.10, 0.002, 0.004, M["inox"]))
    # chuveiro de teto/parede (latão)
    cx = (x0 + x1) / 2
    sgn = 1 if y_glass < y_wall else -1
    o.append(cylinder(name + "_braco", 0.012, 0.30, (cx, y_wall, 2.15), 12, M["latao"], axis="Y"))
    o[-1].rotation_euler = (math.radians(90 if sgn < 0 else -90), 0, 0); o[-1].location = (cx, y_wall, 2.15)
    o.append(cylinder(name + "_ducha", 0.12, 0.012, (cx, y_wall - sgn * 0.30, 2.12), 48, M["latao"]))
    o.append(box(name + "_registro", cx - 0.035, cx + 0.035, y_wall - sgn * 0.01 - 0.005, y_wall - sgn * 0.01 + 0.005, 1.15, 1.22, M["latao"], bevel=0.003))
    return o

def toalheiro(name, M, loc, rot=0, w=0.6):
    o = [cylinder(name + "_barra", 0.01, w, (-w / 2, -0.06, 1.15), 12, M["latao"], axis="X"),
         rb(name + "_toalha", -w / 2 + 0.05, w / 2 - 0.05, -0.08, -0.04, 0.65, 1.16, M["linho_branco"], 0.01)]
    for x in (-w / 2, w / 2):
        o.append(cylinder(f"{name}_sup{x}", 0.008, 0.06, (x, -0.06, 1.15), 8, M["latao"], axis="Y"))
        o[-1].rotation_euler = (math.radians(-90), 0, 0); o[-1].location = (x, 0, 1.15)
    return place(name, o, loc, rot)

# ================================================================ CORTINAS
def cortina(name, M, mat, a0, a1, line, along_x, inner_sign, z0=0.01, z1=2.94, folds=None, amp=0.05):
    """Painel franzido (ondas senoidais) — 'line' é a coordenada do trilho."""
    W = a1 - a0
    n = folds or max(6, int(W / 0.11))
    seg = n * 6
    vs, fs = [], []
    for i in range(seg + 1):
        t = i / seg
        a = a0 + W * t
        off = inner_sign * (0.12 + amp * (1 + math.sin(t * n * 2 * math.pi)) / 2)
        for z in (z0, z1):
            if along_x:
                vs.append((a, line + off, z))
            else:
                vs.append((line + off, a, z))
    for i in range(seg):
        fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    ob = mesh_obj(name, vs, fs, mat)
    for p in ob.data.polygons:
        p.use_smooth = True
    sol = ob.modifiers.new("Espessura", "SOLIDIFY"); sol.thickness = 0.003
    ob["categoria"] = "proposta"
    return ob
