"""Anotações das pranchas 3D (alçados, cortes, planta): cotas, níveis, títulos e nomes.

Todas as cotas mostradas são valores DOCUMENTADOS no PDF (laje 15,35 x 13,10; níveis dos
cortes 0,00 / 2,10 / 2,90 / 3,20 / 3,40). Coleções ficam ocultas no render, exceto nos
modos 'elev', 'corte' e 'planta_vazia' (scripts/render_stills.py).
"""
import math
import bpy
from mathutils import Vector, Matrix
from .core import coll, box, mesh_obj, link

TINTA = None

def _mat():
    global TINTA
    m = bpy.data.materials.get("Tinta de prancha")
    if m is None:
        m = bpy.data.materials.new("Tinta de prancha")
        try:
            m.use_nodes = True
        except Exception:
            pass
        p = m.node_tree.nodes.get("Principled BSDF")
        p.inputs["Base Color"].default_value = (0, 0, 0, 1)
        p.inputs["Emission Color"].default_value = (0.06, 0.06, 0.065, 1)
        p.inputs["Emission Strength"].default_value = 1.0
        p.inputs["Roughness"].default_value = 1.0
        p.inputs["Specular IOR Level"].default_value = 0.0   # sem reflexo do céu: tinta sempre escura
        m["tex_m"] = 1.0
    TINTA = m
    return m

# vistas: direção do olhar d (horizontal) -> direita r = d x Z
VISTAS = {
    "leste":  {"d": Vector((-1, 0, 0)), "plano": 15.0, "titulo": "ALÇADO FRONTAL — FACHADA LESTE"},
    "norte":  {"d": Vector((0, -1, 0)), "plano": 1.9, "titulo": "ALÇADO LATERAL DIREITO — FACHADA NORTE"},
    "sul":    {"d": Vector((0, 1, 0)), "plano": -12.6, "titulo": "ALÇADO LATERAL ESQUERDO — FACHADA SUL"},
    "oeste":  {"d": Vector((1, 0, 0)), "plano": -1.9, "titulo": "ALÇADO POSTERIOR — FACHADA OESTE"},
}
LAJE_X = (-1.125, 14.225)
LAJE_Y = (-12.05, 1.05)

class Plano2D:
    """Desenha em coordenadas (u, v) de um plano vertical perpendicular a d."""
    def __init__(self, d, plano, C, prefixo):
        self.d = d.normalized()
        self.r = self.d.cross(Vector((0, 0, 1))).normalized()
        self.C = C
        self.pref = prefixo
        self.n = 0
        # ponto de referência do plano: coordenada 'plano' no eixo de d
        if abs(self.d.x) > 0.5:
            self.base = Vector((plano, 0, 0))
        else:
            self.base = Vector((0, plano, 0))
        rot = Matrix((self.r, Vector((0, 0, 1)), -self.d)).transposed()
        self.rot = rot.to_quaternion()

    def P(self, u, v):
        # u medido ao longo de r a partir da origem do mundo
        b = self.base - self.r * self.base.dot(self.r)
        return b + self.r * u + Vector((0, 0, v))

    def u_de(self, x, y):
        return Vector((x, y, 0)).dot(self.r)

    def seg(self, u0, v0, u1, v1, w=0.022):
        a, b = self.P(u0, v0), self.P(u1, v1)
        dirv = (b - a)
        L = dirv.length
        if L < 1e-6:
            return
        dn = dirv / L
        perp = (-self.d).cross(dn).normalized() * (w / 2)
        th = -self.d * 0.002
        vs = [a - perp, b - perp, b + perp, a + perp]
        vs += [x + th for x in vs]
        f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        self.n += 1
        ob = mesh_obj(f"{self.pref}_traco{self.n}", vs, f, TINTA, self.C)
        ob["keep_uv"] = 1
        return ob

    def texto(self, body, u, v, size=0.28, align="CENTER", rot90=False):
        cu = bpy.data.curves.new(f"{self.pref}_txt{self.n}", "FONT")
        cu.body = body
        cu.size = size
        cu.align_x = align
        cu.align_y = "CENTER"
        ob = bpy.data.objects.new(f"{self.pref}_txt{self.n}", cu)
        self.n += 1
        ob.data.materials.append(TINTA)
        q = self.rot
        if rot90:
            q = q @ Matrix.Rotation(math.pi / 2, 4, "Z").to_quaternion()
        ob.matrix_world = Matrix.LocRotScale(self.P(u, v) - self.d * 0.003, q, None)
        link(ob, self.C)
        return ob

    def cota_h(self, u0, u1, v, rotulo, ext_de=None):
        self.seg(u0, v, u1, v)
        for u in (u0, u1):
            self.seg(u - 0.09, v - 0.09, u + 0.09, v + 0.09, 0.03)   # tique a 45°
            if ext_de is not None:
                self.seg(u, ext_de, u, v + 0.15, 0.012)
        self.texto(rotulo, (u0 + u1) / 2, v + 0.28)

    def cota_v(self, u, v0, v1, rotulo, ext_de=None):
        self.seg(u, v0, u, v1)
        for v in (v0, v1):
            self.seg(u - 0.09, v - 0.09, u + 0.09, v + 0.09, 0.03)
            if ext_de is not None:
                self.seg(ext_de, v, u + 0.15, v, 0.012)
        self.texto(rotulo, u - 0.32, (v0 + v1) / 2, rot90=True)

    def nivel(self, u, v, rotulo):
        s = 0.16
        self.seg(u - s, v + s, u, v, 0.02); self.seg(u, v, u + s, v + s, 0.02); self.seg(u - s, v + s, u + s, v + s, 0.02)
        self.seg(u + s, v, u + 0.9, v, 0.012)
        self.texto(rotulo, u + 0.28, v + 0.16, 0.2, "LEFT")

    def escala(self, u, v):
        """Escala gráfica 0–1–2–5 m."""
        self.seg(u, v, u + 5, v, 0.03)
        for k, m in enumerate((0, 1, 2, 5)):
            self.seg(u + m, v - 0.1, u + m, v + 0.1, 0.02)
            self.texto(f"{m}", u + m, v - 0.32, 0.2)
        self.seg(u, v + 0.05, u + 1, v + 0.05, 0.09)
        self.seg(u + 2, v + 0.05, u + 5, v + 0.05, 0.09)
        self.texto("m", u + 5.35, v - 0.32, 0.2)

NIVEIS = [(0.0, "±0,00 piso"), (2.10, "+2,10 portas"), (2.90, "+2,90 vidros"), (3.40, "+3,40 laje")]

def alcado(nome, C):
    V = VISTAS[nome]
    D = Plano2D(V["d"], V["plano"], C, "Cota_" + nome)
    us = [D.u_de(x, y) for x in LAJE_X for y in LAJE_Y]
    u0, u1 = min(us), max(us)
    largura = u1 - u0
    D.cota_h(u0, u1, 4.15, f"{largura:.2f}".replace(".", ",") + " m (laje)", ext_de=3.5)
    D.cota_v(u0 - 0.6, 0.0, 3.40, "3,40 m", ext_de=u0 - 0.1)
    for z, t in NIVEIS:
        D.nivel(u1 + 0.45, z, t)
    D.seg(u0 - 1.2, -0.05, u1 + 1.6, -0.05, 0.035)   # linha do terreno
    D.texto(V["titulo"], (u0 + u1) / 2, -0.85, 0.42)
    D.escala(u0, -1.6)
    D.texto("Medidas do projeto (PDF). Revestimentos e ambientação: proposta.", u1 - 3.2, -1.6, 0.17)

def corte(nome, d, plano_cam, titulo, C):
    D = Plano2D(d, plano_cam, C, "Cota_" + nome)
    us = [D.u_de(x, y) for x in LAJE_X for y in LAJE_Y]
    u0, u1 = min(us), max(us)
    for z, t in [(0.0, "±0,00 piso"), (2.10, "+2,10 portas"), (3.05, "+3,05 forro"), (3.40, "+3,40 laje")]:
        D.nivel(u1 + 0.45, z, t)
    D.seg(u0 - 1.2, -0.05, u1 + 1.6, -0.05, 0.035)
    D.texto(titulo, (u0 + u1) / 2, -0.85, 0.42)
    D.escala(u0, -1.6)

ROTULOS_Z = 0.004
ROTULOS = [("SALA DE JANTAR", 1.45, -0.75), ("COZINHA", 4.05, -0.55), ("DESPENSA", 7.42, -2.05), ("WC", 7.42, -3.85),
           ("GARAGEM", 10.85, -2.4), ("CORREDOR", 9.6, -5.35), ("SALA DE ESTAR", 2.6, -7.0), ("SUÍTE", 6.8, -8.45),
           ("WC", 9.15, -7.35), ("WC", 9.15, -9.95), ("SUÍTE", 11.5, -8.45), ("ÁREA DE SERVIÇO", 2.6, -11.05),
           ("ENTRADA", 14.45, -5.35)]

def planta(C):
    # nomes dos ambientes (texto deitado no piso, lido de cima com o norte para cima)
    for k, (t, x, y) in enumerate(ROTULOS):
        cu = bpy.data.curves.new(f"Rotulo_{k}", "FONT")
        cu.body = t; cu.size = 0.36 if len(t) < 14 else 0.28
        cu.align_x = "CENTER"; cu.align_y = "CENTER"
        ob = bpy.data.objects.new(f"Rotulo_{k}", cu)
        ob.data.materials.append(TINTA)
        ob.location = (x, y, ROTULOS_Z if y > -10.7 else -0.045)
        if t == "ENTRADA":
            ob.rotation_euler = (0, 0, math.pi / 2)
        link(ob, C)
    # cotas gerais da laje (documentadas)
    def s(a, b, w=0.025):
        a, b = Vector(a), Vector(b)
        d = (b - a); L = d.length; dn = d / L
        p = Vector((-dn.y, dn.x, 0)) * w / 2
        vs = [a - p, b - p, b + p, a + p]
        ob = mesh_obj("Cota_planta_traco", [tuple(v) for v in vs], [(0, 1, 2, 3)], TINTA, C)
        ob["keep_uv"] = 1
    z = -0.045   # logo acima do piso externo (-0,05): sem sombra deslocada
    (x0, x1), (y0, y1) = LAJE_X, LAJE_Y
    yv = y1 + 0.75; xv = x0 - 0.75   # cota vertical no lado oeste (o leste tem canteiro)
    s((x0, yv, z), (x1, yv, z))
    s((xv, y0, z), (xv, y1, z))
    for x in (x0, x1):
        s((x, y1 + 0.1, z), (x, yv + 0.2, z), 0.012); s((x - 0.1, yv - 0.1, z), (x + 0.1, yv + 0.1, z), 0.03)
    for y in (y0, y1):
        s((xv - 0.2, y, z), (x0 - 0.1, y, z), 0.012); s((xv - 0.1, y - 0.1, z), (xv + 0.1, y + 0.1, z), 0.03)
    for body, loc, rz in (("15,35 m (laje)", ((x0 + x1) / 2, yv + 0.38, z), 0), ("13,10 m (laje)", (xv - 0.38, (y0 + y1) / 2, z), math.pi / 2)):
        cu = bpy.data.curves.new("Cota_planta_txt", "FONT"); cu.body = body; cu.size = 0.34
        cu.align_x = "CENTER"; cu.align_y = "CENTER"
        ob = bpy.data.objects.new("Cota_planta_txt", cu); ob.data.materials.append(TINTA)
        ob.location = loc; ob.rotation_euler = (0, 0, rz); link(ob, C)
    # seta de norte (hipótese: topo da prancha)
    nx, ny = x0 + 0.2, y1 + 1.6
    s((nx, ny - 0.5, z), (nx, ny + 0.5, z), 0.05)
    s((nx - 0.25, ny + 0.2, z), (nx, ny + 0.5, z), 0.05); s((nx + 0.25, ny + 0.2, z), (nx, ny + 0.5, z), 0.05)
    cu = bpy.data.curves.new("Norte_txt", "FONT"); cu.body = "N"; cu.size = 0.4; cu.align_x = "CENTER"
    ob = bpy.data.objects.new("Norte_txt", cu); ob.data.materials.append(TINTA); ob.location = (nx + 0.5, ny, z); link(ob, C)

def planta_cotada(C):
    """Planta humanizada com cotas (estilo da imagem do vídeo). Só medidas documentadas no PDF."""
    zt = 1.25   # acima dos móveis (vista ortográfica de topo não percebe a altura)
    def s(a, b, w=0.05):
        a, b = Vector(a), Vector(b); d = (b - a); L = d.length; dn = d / L
        p = Vector((-dn.y, dn.x, 0)) * w / 2
        ob = mesh_obj("Cota_pc_traco", [tuple(v) for v in (a - p, b - p, b + p, a + p)], [(0, 1, 2, 3)], TINTA, C)
        ob["keep_uv"] = 1; ob.visible_shadow = False
    def t(body, x, y, rz=0, size=0.55):
        cu = bpy.data.curves.new("Cota_pc_txt", "FONT"); cu.body = body; cu.size = size
        cu.align_x = "CENTER"; cu.align_y = "CENTER"
        ob = bpy.data.objects.new("Cota_pc_txt", cu); ob.data.materials.append(TINTA)
        ob.location = (x, y, zt); ob.rotation_euler = (0, 0, rz); ob.visible_shadow = False; link(ob, C)
    def ch(x0, x1, y, rot, z=zt):   # cota horizontal
        s((x0, y, z), (x1, y, z)); s((x0 - 0.12, y - 0.12, z), (x0 + 0.12, y + 0.12, z), 0.05); s((x1 - 0.12, y - 0.12, z), (x1 + 0.12, y + 0.12, z), 0.05)
        t(rot, (x0 + x1) / 2, y + 0.35)
    def cv(y0, y1, x, rot, z=zt):
        s((x, y0, z), (x, y1, z)); s((x - 0.12, y0 - 0.12, z), (x + 0.12, y0 + 0.12, z), 0.05); s((x - 0.12, y1 - 0.12, z), (x + 0.12, y1 + 0.12, z), 0.05)
        t(rot, x - 0.35, (y0 + y1) / 2, math.pi / 2)
    (x0, x1), (y0, y1) = LAJE_X, LAJE_Y
    ch(x0, x1, y1 + 0.9, "15,35 m")
    cv(y0, y1, x1 + 1.1, "13,10 m")
    ch(0.10, 5.10, -12.85, "5,00 m")
    ch(5.30, 8.30, -12.85, "3,00 m"); ch(8.50, 9.80, -12.85, "1,30 m"); ch(10.00, 13.00, -12.85, "3,00 m")
    cv(-5.85, -4.85, 13.55, "1,00 m")
    ch(3.50, 4.60, -0.75, "1,10 m")
    ch(-6.60, -4.10, 1.95, "2,50 m"); cv(-9.60, -0.10, -7.35, "9,50 m")
    lx0, lx1, ly0, ly1 = -8.45, 21.55, -18.0, 7.0
    ch(lx0, lx1, ly1 + 0.7, "30,00 m (lote)"); cv(ly0, ly1, lx0 - 0.7, "25,00 m (lote)")

def build():
    _mat()
    CA = coll("15_Cotas_Alcados"); CA.hide_render = True
    CC = coll("15_Cotas_Cortes"); CC.hide_render = True
    CP = coll("15_Rotulos_Planta"); CP.hide_render = True
    for n in VISTAS:
        sub = coll(f"15a_Cotas_{n}", CA)
        alcado(n, sub)
    corte("corte_long", Vector((0, 1, 0)), -2.55, "CORTE LONGITUDINAL — JANTAR, COZINHA, DESPENSA E GARAGEM", coll("15b_Cotas_corte_long", CC))
    corte("corte_transv", Vector((-1, 0, 0)), 7.65, "CORTE TRANSVERSAL — SUÍTE 2, CORREDOR, WC E DESPENSA", coll("15b_Cotas_corte_transv", CC))
    planta(CP)
    CQ = coll("15_Cotas_Planta"); CQ.hide_render = True
    planta_cotada(CQ)
    # captador de sombra para pranchas com fundo branco
    for o in list(CA.all_objects) + list(CC.all_objects) + list(CP.all_objects) + list(CQ.all_objects):
        o.visible_shadow = False
    sc_ = box("Captador_sombra_pranchas", -60, 60, -60, 60, -0.06, -0.049, None, coll("15_Pranchas_Apoio"))
    sc_.is_shadow_catcher = True
    sc_.hide_render = True
