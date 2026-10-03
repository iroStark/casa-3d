"""Implantação: lote (folha 02 editada, 30 x 25 m), piscina 2,50 x 9,50 (cotada),
terraço, acessos, muro (H), vegetação. Itens não documentados recebem status 'H' ou 'P'.
"""
import math, random
import bpy
from mathutils import Vector
from .core import coll, set_coll, box, mesh_obj, cylinder, sphere, group
from .arch import DATA
from . import furn as F

LOT_X = (-8.45, 21.55)
LOT_Y = (-18.0, 7.0)
POOL = dict(x=(-6.60, -4.10), y=(-9.60, -0.10), depth=1.40)
SURR = dict(x=(-7.475, -3.225), y=(-11.15, 1.45))   # contorno do entorno da piscina (pág. 2, G)

def tag(objs, status, cat="paisagismo", fonte=None):
    for o in objs:
        o["status"] = status; o["categoria"] = cat
        if fonte:
            o["fonte"] = fonte
    return objs

def rect_minus(outer, holes):
    """Divide um retângulo em faixas que evitam retângulos-furo (todos alinhados)."""
    (x0, x1), (y0, y1) = outer
    xs = sorted({x0, x1} | {h[0][0] for h in holes} | {h[0][1] for h in holes})
    ys = sorted({y0, y1} | {h[1][0] for h in holes} | {h[1][1] for h in holes})
    xs = [x for x in xs if x0 <= x <= x1]; ys = [y for y in ys if y0 <= y <= y1]
    cells = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx = (xs[i] + xs[i + 1]) / 2; cy = (ys[j] + ys[j + 1]) / 2
            if any(h[0][0] <= cx <= h[0][1] and h[1][0] <= cy <= h[1][1] for h in holes):
                continue
            cells.append(((xs[i], xs[i + 1]), (ys[j], ys[j + 1])))
    return cells

def tree(name, M, loc, h=6.0, crown=2.6, seed=1, flowers=None, leaves=2600, casca=None, folha=(0.30, 0.22), z0=-0.22):
    """Árvore (proposta): tronco + galhos até pontas onde se agrupam as folhas."""
    rr = random.Random(seed)
    o = []
    x, y = loc[0], loc[1]
    trunk_h = h * 0.42
    o.append(cylinder(name + "_tronco", 0.17, trunk_h - z0, (x, y, z0), 12, casca or M["tronco"], r2=0.11))
    tips = []
    nb = 7
    for k in range(nb):
        a = k * 2 * math.pi / nb + rr.uniform(-0.3, 0.3)
        base = Vector((x, y, trunk_h - 0.15))
        L = h * rr.uniform(0.32, 0.42)
        d = Vector((math.cos(a) * 0.75, math.sin(a) * 0.75, 1.0)).normalized()
        br = cylinder(f"{name}_galho{k}", 0.08, L, (0, 0, 0), 8, casca or M["tronco"], r2=0.03)
        br.location = base
        br.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        o.append(br)
        end = base + d * L
        for j in range(4):
            tips.append(end + Vector((rr.uniform(-.8, .8), rr.uniform(-.8, .8), rr.uniform(-.3, .6))) * crown * 0.35)
    per = max(30, leaves // len(tips))
    o += F.foliage(name + "_copa", M, tips, folha[0], folha[1], per, crown * 0.42, seed, droop=0.25)
    if flowers:
        o += F.foliage(name + "_flores", M, tips[::2], 0.10, 0.08, per // 3, crown * 0.36, seed + 1, mat=flowers, droop=0.1)
    e = group(name, o)
    tag(o + [e], "P", fonte="Proposta de paisagismo (não documentada no PDF)")
    return e

def shrub_row(name, M, x0, x1, y0, y1, seed=3, density=4.0):
    """Maciço de arbustos: aglomerados densos de folhas pequenas sobre o solo."""
    rr = random.Random(seed)
    n = max(2, int((abs(x1 - x0) + abs(y1 - y0)) * density))
    clusters = []
    for i in range(n):
        clusters.append((rr.uniform(x0, x1), rr.uniform(y0, y1), rr.uniform(0.25, 0.5)))
    o = F.foliage(name, M, clusters, 0.20, 0.14, 300, 0.40, seed, mat=M["folha"], droop=-0.2)
    e = group(name, o)
    tag(o + [e], "P")
    return e

def lounger(name, M, loc, rot=0):
    o = [F.rb(name + "_estrutura", -0.32, 0.32, -0.95, 0.95, 0.18, 0.30, M["deck"], 0.01),
         F.rb(name + "_colchonete", -0.30, 0.30, -0.93, 0.45, 0.30, 0.38, M["linho_branco"], 0.03),
         F.rb(name + "_encosto", -0.30, 0.30, 0.42, 0.95, 0.30, 0.38, M["linho_branco"], 0.03)]
    o[-1].rotation_euler = (math.radians(35), 0, 0)
    o[-1].location = (0, -0.25, 0.25)
    for x in (-0.28, 0.28):
        for y in (-0.88, 0.88):
            o.append(box(f"{name}_pe{x}{y}", x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0, 0.18, M["deck"]))
    return F.place(name, o, loc, rot)

PAVIMENTO = [((-1.60, 14.70), (-12.55, 1.55)), ((14.70, 21.55), (-4.85, 0.40)), ((-7.475, -1.60), (-11.15, 1.45))]
def chao_z(x, y):
    """Cota do chão: -0,05 na plataforma/pavimentos, -0,22 no gramado."""
    return -0.05 if any(a <= x <= b and c <= y <= d for (a, b), (c, d) in PAVIMENTO) else -0.22

def build(L):
    M = L
    if "folha_arbusto" not in M:
        from .mats import pbr
        M["folha_arbusto"] = pbr("Arbusto (massa verde)", (0.13, 0.22, 0.09), 0.85, tex="grass_col", tex_m=0.6, tint=(0.55, 0.7, 0.5), categoria="paisagismo")
        M["grama_campo"] = pbr("Campo (entorno)", (0.3, 0.36, 0.2), 0.95, tex="grass_col", tex_m=6.0, tint=(0.62, 0.62, 0.55), categoria="paisagismo")
        M["flor_amarela"] = pbr("Flor de ipê amarelo", (0.95, 0.72, 0.12), 0.6, tex="leaves_col", tex_m=1.0, tint=(4.0, 2.6, 0.5), alpha_tex=True, categoria="paisagismo")
    root = coll("ENTORNO")
    C = coll("01_Terreno_e_Implantacao", root)
    set_coll(C)
    # ---------------- gramado com furos (terraço, piscina, acesso)
    terr = (( -1.60, 14.70), (-12.55, 1.55))
    drive = ((14.70, LOT_X[1]), (-4.85, 0.40))
    holes = [terr, (SURR["x"], SURR["y"]), drive, ((SURR["x"][1], terr[0][0]), SURR["y"])]
    g = []
    for k, ((a, b), (c, d)) in enumerate(rect_minus((LOT_X, LOT_Y), holes)):
        g.append(box(f"Gramado_{k}", a, b, c, d, -0.40, -0.22, M["grama"]))
    tag(g, "P (lote: C 30 x 25) / H: gramado 17 cm abaixo da plataforma (vídeo)")
    # ---------------- terraço em pedra sob o beiral (H: largura do passeio)
    t = [box("Terraco_pedra", terr[0][0], terr[0][1], terr[1][0], terr[1][1], -0.30, -0.05, M["concreto_claro"])]
    tag(t, "H (passeio ao redor da casa; contorno tracejado da pág. 2)", "acabamento")
    # ---------------- acesso de veículos (P) e caminho até a piscina
    a = [box("Acesso_veiculos", drive[0][0], drive[0][1], drive[1][0], drive[1][1], -0.30, -0.05, M["calcada"])]
    for k in range(5):
        x = -1.60 - 0.30 - k * 0.0
    # piso cimentício claro ligando o terraço ao entorno da piscina (pág. 26 / vídeo)
    a.append(box("Piso_ligacao_piscina", SURR["x"][1], terr[0][0], SURR["y"][0], SURR["y"][1], -0.30, -0.05, M["concreto_claro"]))
    tag(a, "P")
    # ---------------- piscina 2,50 x 9,50 (C) — casco com profundidade real (H 1,40)
    set_coll(coll("01b_Piscina", root))
    (px0, px1), (py0, py1) = POOL["x"], POOL["y"]
    D = POOL["depth"]
    zt = -0.05; zb = zt - D
    v = [(px0, py0, zb), (px1, py0, zb), (px1, py1, zb), (px0, py1, zb),
         (px0, py0, zt), (px1, py0, zt), (px1, py1, zt), (px0, py1, zt)]
    f = [(0, 1, 2, 3), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    shell = mesh_obj("Piscina_casco_pastilha", v, f, M["pastilha"])
    # degraus de entrada (H) no lado norte
    steps = []
    for k in range(3):
        steps.append(box(f"Piscina_degrau{k}", px0, px1, py1 - 0.35 * (k + 1), py1 - 0.35 * k if k else py1,
                         zb, zt - 0.40 * (k + 1), M["pastilha"]))
    water = box("Piscina_agua", px0 + 0.001, px1 - 0.001, py0 + 0.001, py1 - 0.001, zb + 0.01, -0.13, M["agua"])
    water["status"] = "C dimensão / H nível d'água"
    cop = []
    cw = 0.35
    cop.append(box("Borda_N", px0 - cw, px1 + cw, py1, py1 + cw, -0.30, -0.03, M["borda_piscina"]))
    cop.append(box("Borda_S", px0 - cw, px1 + cw, py0 - cw, py0, -0.30, -0.03, M["borda_piscina"]))
    cop.append(box("Borda_O", px0 - cw, px0, py0, py1, -0.30, -0.03, M["borda_piscina"]))
    cop.append(box("Borda_L", px1, px1 + cw, py0, py1, -0.30, -0.03, M["borda_piscina"]))
    # entorno: pedra a oeste/norte/sul + deck de cumaru a leste (P)
    sx0, sx1 = SURR["x"]; sy0, sy1 = SURR["y"]
    cop.append(box("Entorno_O", sx0, px0 - cw, sy0, sy1, -0.30, -0.05, M["piso_externo"]))
    cop.append(box("Entorno_N", px0 - cw, sx1, py1 + cw, sy1, -0.30, -0.05, M["piso_externo"]))
    cop.append(box("Entorno_S", px0 - cw, sx1, sy0, py0 - cw, -0.30, -0.05, M["piso_externo"]))
    deck = box("Deck_madeira", px1 + cw, sx1, py0 - cw, py1 + cw, -0.30, -0.04, M["deck"])
    deck["status"] = "P (pág. 26 mostra deck; folha 02 mostra apenas contorno)"
    tag([shell, water] + steps, "C 2,50 x 9,50 (pág. 2) / posição G / profundidade H", "arquitetura")
    tag(cop, "G contorno / P material", "acabamento")
    lounger("Espreguicadeira_1", M, (-4.75, -10.55), 90)
    lounger("Espreguicadeira_2", M, (-6.45, -10.55), 90)
    F.mesa_lateral("Mesa_piscina", M, (-5.60, -10.55), h=0.45)
    # guarda-sol
    gs = [cylinder("Guarda_sol_haste", 0.025, 2.4, (-3.75, -6.0, -0.05), 12, M["deck"]),
          cylinder("Guarda_sol_lona", 1.3, 0.35, (-3.75, -6.0, 2.05), 24, M["linho_branco"], r2=0.05),
          cylinder("Guarda_sol_base", 0.25, 0.08, (-3.75, -6.0, -0.05), 24, M["vaso"])]
    for o_ in gs:   # sem guarda-sol (não aparece no vídeo)
        bpy.data.objects.remove(o_, do_unlink=True)
    # ---------------- muro (H) com portão de correr ripado a leste (P)
    set_coll(coll("01c_Muro_e_Portao", root))
    mh = 2.0; mt = 0.15
    (lx0, lx1), (ly0, ly1) = LOT_X, LOT_Y
    mu = [box("Muro_N", lx0, lx1, ly1 - mt, ly1, -0.30, mh, M["parede_ext"]),
          box("Muro_S", lx0, lx1, ly0, ly0 + mt, -0.30, mh, M["parede_ext"]),
          box("Muro_O", lx0, lx0 + mt, ly0, ly1, -0.30, mh, M["parede_ext"]),
          box("Muro_L_sul", lx1 - mt, lx1, ly0, -7.30, -0.30, mh, M["parede_ext"]),
          box("Muro_L_meio", lx1 - mt, lx1, -6.10, drive[1][0], -0.30, mh, M["parede_ext"]),
          box("Muro_L_norte", lx1 - mt, lx1, drive[1][1], ly1, -0.30, mh, M["parede_ext"])]
    tag(mu, "H (contorno do lote desenhado sem altura; adotado 2,00 m)", "arquitetura")
    gate = []
    gy0, gy1 = drive[1]
    n = int((gy1 - gy0) / 0.12)
    for k in range(n):
        y = gy0 + k * (gy1 - gy0) / n
        gate.append(box(f"Portao_ripa{k}", lx1 - 0.10, lx1 - 0.04, y + 0.01, y + 0.10, 0.05, mh - 0.05, M["deck"]))
    gate.append(box("Portao_trilho", lx1 - 0.12, lx1 - 0.02, gy0, gy1, -0.06, 0.05, M["ferro"]))
    gate.append(box("Portao_pedestre", lx1 - 0.10, lx1 - 0.04, -7.25, -6.15, 0.0, mh - 0.05, M["painel_taupe"]))
    tag(gate, "P")
    # ---------------- vegetação: vasos com palmeiras nas posições das fachadas CAD (pág. 1)
    set_coll(coll("11_Paisagismo", root))
    pots = [(13.75, -10.17), (13.75, -6.40), (5.67, 0.55), (-0.55, 0.55), (0.37, -10.40), (4.95, -10.40), (9.15, -11.95), (-0.55, -10.60)]
    for k, (x, y) in enumerate(pots):
        e = F.planta_vaso(f"Vaso_palmeira_fachada_{k+1}", M, (x, y, -0.05), h=1.5, pot_r=0.24, kind="palmeira", leaves=22, seed=40 + k, pot=M["vaso"])
        e["status"] = "X — vasos com palmeiras desenhados nas fachadas CAD (pág. 1)"
        e["categoria"] = "paisagismo"
    # vídeo: muro coberto de trepadeira (faces internas), dracenas, poltronas verde-água no terraço
    (lx0, lx1), (ly0, ly1) = LOT_X, LOT_Y
    t_ = 0.04
    verde = [box("Trepadeira_muro_N", lx0 + 0.15, lx1 - 0.15, ly1 - 0.15 - t_, ly1 - 0.15, -0.24, 2.05, M["muro_verde"]),
             box("Trepadeira_muro_S", lx0 + 0.15, lx1 - 0.15, ly0 + 0.15, ly0 + 0.15 + t_, -0.24, 2.05, M["muro_verde"]),
             box("Trepadeira_muro_O", lx0 + 0.15, lx0 + 0.15 + t_, ly0 + 0.15, ly1 - 0.15, -0.24, 2.05, M["muro_verde"])]
    tag(verde, "P — muro verde do vídeo de referência")
    for k, (x, y, h) in enumerate([(-3.0, 0.6, 3.4), (-7.5, -12.4, 3.0), (-0.5, -14.6, 2.8), (-7.6, 3.8, 3.2)]):
        F.dracena(f"Dracena_{k}", M, (x, y, chao_z(x, y)), h=h, troncos=4, seed=60 + k)
    F.poltrona_barril("Poltrona_terraco_1", M, (-0.95, -4.35), 90)
    F.poltrona_barril("Poltrona_terraco_2", M, (-0.95, -5.45), 90)
    F.vaso_palha("Vaso_palha_terraco", M, (-0.55, -3.55, -0.05), h=0.8, r=0.22)
    # árvores (P): ipê-amarelo e sombreiros
    tree("Arvore_ipe_amarelo_NE", M, (1.5, 5.3), h=6.5, crown=2.6, seed=21, flowers=M["flor_amarela"], leaves=6000)
    tree("Arvore_sombra_SO", M, (3.0, -15.7), h=7.0, crown=3.0, seed=22, leaves=7000)
    tree("Arvore_sombra_SE", M, (18.4, -14.2), h=6.0, crown=2.6, seed=23, leaves=5500)
    tree("Arvore_ipe_NO", M, (-6.8, 4.6), h=5.5, crown=2.2, seed=24, flowers=M["flor_amarela"], leaves=4500)
    # maciços junto ao muro (P)
    shrub_row("Macico_N", M, -8.0, 21.0, 6.2, 6.7, 31, 1.2)
    shrub_row("Macico_S", M, -8.0, 21.0, -17.7, -17.2, 32, 1.2)
    shrub_row("Macico_O", M, -8.1, -7.7, -17.0, 6.0, 33, 1.2)
    shrub_row("Macico_L", M, 21.0, 21.3, -17.0, -6.0, 34, 1.2)
    # jardim de entrada (vídeo): placas-degrau flutuantes com balizadores, touceiras e árvore de tronco claro
    pl = []
    for k, (xc, yc, w) in enumerate([(20.55, -6.70, 2.4), (19.45, -6.45, 2.6), (18.35, -6.15, 2.4), (17.25, -5.90, 2.6), (16.15, -5.62, 2.4), (15.20, -5.40, 2.2)]):
        pl.append(box(f"Placa_degrau_{k}", xc - 0.42, xc + 0.42, yc - w / 2, yc + w / 2, -0.15, -0.06, M["concreto_claro"]))
        for yy in (yc - w / 2 + 0.12, yc + w / 2 - 0.12):
            lz = box(f"Placa_degrau_{k}_luz{yy:.2f}", xc + 0.28, xc + 0.36, yy - 0.04, yy + 0.04, -0.06, -0.035, M["led"])
            lz["luz"] = 1; pl.append(lz)
    tag(pl, "P — placas-degrau do vídeo")
    tree("Arvore_tronco_claro_E", M, (17.6, -9.3), h=6.2, crown=2.4, seed=25, leaves=5000, casca=M["casca_clara"], folha=(0.22, 0.06))
    for k, (x, y, r) in enumerate([(16.4, -8.4, 0.5), (17.1, -8.0, 0.42), (16.9, -9.2, 0.55), (18.4, -8.6, 0.45), (16.1, -9.6, 0.4), (18.9, -9.9, 0.5)]):
        F.touceira(f"Touceira_{k}", M, (x, y, -0.22), r=r, seed=80 + k)
    shrub_row("Canteiro_caminho", M, 15.2, 21.0, -7.65, -7.35, 35, 2.0)
    # ---------------- calçada/rua fora do lote (contexto neutro, H)
    set_coll(C)
    street = [box("Calcada_publica", LOT_X[1], LOT_X[1] + 2.5, LOT_Y[0] - 4, LOT_Y[1] + 4, -0.30, -0.02, M["calcada"]),
              box("Rua", LOT_X[1] + 2.5, LOT_X[1] + 10, LOT_Y[0] - 4, LOT_Y[1] + 4, -0.40, -0.17, M["impermeab"]),
]
    for k, ((a0, a1), (b0, b1)) in enumerate(rect_minus(((LOT_X[0] - 400, LOT_X[1] + 400), (LOT_Y[0] - 400, LOT_Y[1] + 400)), [((LOT_X[0], LOT_X[1]), (LOT_Y[0], LOT_Y[1]))])):
        street.append(box(f"Entorno_vizinho_{k}", a0, a1, b0, b1, -0.52, -0.42, M["grama_campo"]))
    tag(street, "H — contexto genérico fora do lote (rua a leste suposta pelo acesso da garagem)")
