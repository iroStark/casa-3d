"""Câmeras do projeto. Interiores com câmera nivelada (pitch 0) e deslocamento de lente
(shift) para manter verticais retas; lentes 20–35 mm para não exagerar os espaços.

Cada entrada: id, ambiente, titulo, loc (x,y,z), alvo (x,y[,z]), lente, shift_y, modo
modo: 'dia' | 'tarde' (entardecer) | 'planta' | 'aereo'
"""
import math
import bpy
from mathutils import Vector
from .core import coll, link

CAMS = [
    # ---------------- EXTERIORES
    dict(id="E01", amb="Fachada leste (entrada e garagem)", loc=(20.6, -10.6, 1.60), alvo=(10.0, -2.4), lente=26, shift=0.10, modo="dia"),
    dict(id="E02", amb="Fachada norte e garagem aberta", loc=(17.4, 5.9, 1.60), alvo=(5.0, -3.0), lente=26, shift=0.10, modo="dia"),
    dict(id="E03", amb="Fachada oeste e piscina", loc=(-7.6, -15.6, 1.65), alvo=(0.0, -3.0), lente=26, shift=0.08, modo="dia"),
    dict(id="E04", amb="Piscina e salas integradas", loc=(-7.9, 2.6, 1.60), alvo=(1.0, -7.2), lente=24, shift=0.06, modo="dia"),
    dict(id="E05", amb="Fachada sul (suítes)", loc=(10.4, -17.4, 1.60), alvo=(5.8, -9.0), lente=24, shift=0.10, modo="dia"),
    dict(id="E06", amb="Vista aérea nordeste", loc=(27.0, 15.5, 13.5), alvo=(6.0, -5.5, 0.0), lente=32, shift=0.0, modo="aereo"),
    dict(id="E07", amb="Vista aérea sudoeste", loc=(-16.5, -27.5, 14.0), alvo=(5.5, -4.5, 0.0), lente=32, shift=0.0, modo="aereo"),
    dict(id="E08", amb="Cobertura (vista superior)", loc=(6.55, -5.5, 40.0), alvo=(6.55, -5.5, 0.0), lente=50, shift=0.0, modo="topo", ortho=31.0),
    dict(id="E09", amb="Entrada ao entardecer", loc=(20.6, -10.6, 1.60), alvo=(10.0, -2.4), lente=26, shift=0.10, modo="tarde"),
    dict(id="E10", amb="Piscina ao entardecer", loc=(-7.9, 2.6, 1.60), alvo=(1.0, -7.2), lente=24, shift=0.06, modo="tarde"),
    dict(id="E11", amb="Vista aérea ao entardecer", loc=(27.0, 15.5, 13.5), alvo=(6.0, -5.5, 0.0), lente=32, shift=0.0, modo="aereo_tarde"),
    dict(id="E12", amb="Fachada oeste ao entardecer", loc=(-7.6, -15.6, 1.65), alvo=(0.0, -3.0), lente=26, shift=0.08, modo="tarde"),
    # ---------------- SALA DE ESTAR
    dict(id="I01", amb="Sala de estar", loc=(4.80, -5.30, 1.45), alvo=(1.2, -8.8), lente=22, shift=0.02, modo="dia"),
    dict(id="I02", amb="Sala de estar", loc=(0.55, -9.40, 1.40), alvo=(4.2, -5.0), lente=22, shift=0.02, modo="dia"),
    dict(id="I03", amb="Sala de estar", loc=(2.60, -9.15, 1.25), alvo=(2.6, -4.0), lente=24, shift=0.06, modo="dia"),
    dict(id="I04", amb="Sala de estar (detalhe)", loc=(3.70, -6.90, 1.10), alvo=(2.3, -8.4, 0.45), lente=40, shift=0.0, modo="dia", pitch=True),
    # ---------------- JANTAR
    dict(id="D01", amb="Sala de jantar", loc=(3.05, -5.25, 1.50), alvo=(0.6, -0.8), lente=22, shift=0.02, modo="dia"),
    dict(id="D02", amb="Sala de jantar", loc=(0.45, -0.40, 1.55), alvo=(3.6, -4.8), lente=22, shift=0.02, modo="dia"),
    dict(id="D03", amb="Sala de jantar (detalhe)", loc=(2.75, -4.30, 1.35), alvo=(1.4, -2.8, 1.1), lente=35, shift=0.0, modo="dia", pitch=True),
    # ---------------- COZINHA
    dict(id="K01", amb="Cozinha", loc=(1.75, -2.10, 1.50), alvo=(5.8, -3.1), lente=22, shift=0.02, modo="dia"),
    dict(id="K02", amb="Cozinha", loc=(5.45, -0.72, 1.55), alvo=(3.2, -4.6), lente=22, shift=0.02, modo="dia"),
    dict(id="K03", amb="Cozinha (detalhe)", loc=(5.05, -3.55, 1.35), alvo=(3.95, -4.0, 0.92), lente=40, shift=0.0, modo="dia", pitch=True),
    # ---------------- CORREDOR
    dict(id="C01", amb="Corredor e hall", loc=(5.40, -5.35, 1.55), alvo=(13.0, -5.35), lente=24, shift=0.0, modo="dia"),
    dict(id="C02", amb="Corredor e hall", loc=(12.75, -5.40, 1.55), alvo=(4.0, -5.70), lente=24, shift=0.0, modo="dia"),
    # ---------------- SUITE 1
    dict(id="S101", amb="Suíte 1", loc=(10.45, -6.55, 1.50), alvo=(12.6, -9.6), lente=20, shift=0.02, modo="dia"),
    dict(id="S102", amb="Suíte 1", loc=(10.25, -10.85, 1.45), alvo=(12.6, -7.2), lente=20, shift=0.02, modo="dia"),
    dict(id="S103", amb="Suíte 1", loc=(12.30, -7.55, 1.50), alvo=(10.1, -10.9), lente=20, shift=0.02, modo="dia"),
    dict(id="S104", amb="Suíte 1 (detalhe)", loc=(10.85, -8.45, 1.35), alvo=(12.9, -8.1, 0.95), lente=32, shift=0.0, modo="dia", pitch=True),
    # ---------------- SUITE 2
    dict(id="S201", amb="Suíte 2", loc=(7.95, -6.45, 1.50), alvo=(5.6, -9.4), lente=20, shift=0.02, modo="dia"),
    dict(id="S202", amb="Suíte 2", loc=(8.05, -10.85, 1.45), alvo=(5.6, -7.2), lente=20, shift=0.02, modo="dia"),
    dict(id="S203", amb="Suíte 2 (detalhe)", loc=(6.65, -9.30, 1.40), alvo=(8.3, -10.2, 1.30), lente=30, shift=0.0, modo="dia", pitch=True),
    # ---------------- BANHEIROS
    dict(id="B01", amb="Banheiro da suíte 2 (parede em corte)", loc=(6.95, -7.30, 1.50), alvo=(10.5, -7.30), lente=24, shift=0.0, modo="banho", clip=1.58),
    dict(id="B02", amb="Banheiro da suíte 2 (parede em corte)", loc=(9.15, -5.05, 1.50), alvo=(9.15, -9.0), lente=30, shift=0.0, modo="banho", clip=1.05),
    dict(id="B03", amb="Banheiro da suíte 1 (parede em corte)", loc=(11.75, -9.95, 1.50), alvo=(8.0, -9.95), lente=27, shift=0.0, modo="banho", clip=1.98),
    dict(id="B04", amb="Banheiro da suíte 1 (parede em corte)", loc=(9.15, -12.90, 1.50), alvo=(9.15, -8.5), lente=40, shift=0.0, modo="banho", clip=1.72),
    dict(id="B05", amb="WC social (parede em corte)", loc=(7.42, -5.55, 1.50), alvo=(7.42, -2.0), lente=22, shift=0.0, modo="banho", clip=0.95),
    dict(id="B06", amb="WC social (parede em corte)", loc=(10.10, -3.80, 1.50), alvo=(6.0, -3.80), lente=38, shift=0.0, modo="banho", clip=1.86),
    # ---------------- DESPENSA / SERVIÇO / GARAGEM
    dict(id="X01", amb="Despensa (parede em corte)", loc=(10.10, -2.05, 1.50), alvo=(6.0, -2.05), lente=42, shift=0.0, modo="banho", clip=1.86),
    dict(id="X02", amb="Despensa (parede em corte)", loc=(4.95, -2.05, 1.50), alvo=(9.0, -2.05), lente=38, shift=0.0, modo="banho", clip=1.66),
    dict(id="X03", amb="Área de serviço", loc=(1.9, -13.6, 1.60), alvo=(1.9, -10.2, 1.0), lente=28, shift=0.0, modo="dia", pitch=True),
    dict(id="X04", amb="Área de serviço", loc=(4.9, -12.3, 1.50), alvo=(1.5, -10.25, 1.0), lente=24, shift=0.0, modo="dia", pitch=True),
    dict(id="X05", amb="Garagem", loc=(15.6, 1.9, 1.60), alvo=(10.4, -2.6), lente=24, shift=0.06, modo="dia"),
    dict(id="X06", amb="Garagem", loc=(12.7, -4.05, 1.60), alvo=(8.5, -0.4), lente=22, shift=0.04, modo="dia"),
    # ---------------- DETALHES DE MATERIAL
    dict(id="M01", amb="Detalhe: boiserie e cimalha da sala", loc=(3.55, -7.05, 1.40), alvo=(5.10, -8.30, 1.30), lente=35, shift=0.0, modo="dia", pitch=True),
    dict(id="M02", amb="Detalhe: borda da piscina e deck", loc=(-3.6, -9.9, 0.9), alvo=(-5.4, -7.0, -0.2), lente=30, shift=0.0, modo="dia", pitch=True),
    dict(id="M03", amb="Detalhe: treliça iluminada", loc=(6.9, -8.6, 1.45), alvo=(5.3, -7.9, 1.3), lente=30, shift=0.0, modo="tarde_int", pitch=True),
    # ---------------- PLANTAS 3D
    dict(id="P01", amb="Planta 3D mobiliada (topo)", loc=(6.55, -5.5, 30.0), alvo=(6.55, -5.5, 0.0), lente=50, shift=0.0, modo="planta", ortho=16.2),
    dict(id="P02", amb="Planta 3D mobiliada (perspectiva sudeste)", loc=(21.5, -22.0, 17.0), alvo=(6.5, -5.5, 0.0), lente=30, shift=0.0, modo="planta_persp"),
    dict(id="P03", amb="Planta 3D mobiliada (perspectiva noroeste)", loc=(-9.5, 9.0, 16.0), alvo=(6.5, -5.5, 0.0), lente=30, shift=0.0, modo="planta_persp"),
]

def make_camera(c, C):
    name = "CAM_" + c["id"]
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = c["lente"]
    cd.sensor_width = 36
    cd.clip_start = c.get("clip", 0.05)   # >0,05: vista em corte (plano de corte atravessa a parede)
    cd.clip_end = 400
    cd.shift_y = c.get("shift", 0.0)
    if c.get("ortho"):
        cd.type = "ORTHO"; cd.ortho_scale = c["ortho"]
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if ob.name not in C.objects:
        link(ob, C)
    loc = Vector(c["loc"])
    tgt = Vector((c["alvo"][0], c["alvo"][1], c["alvo"][2] if len(c["alvo"]) > 2 else c["loc"][2]))
    ob.location = loc
    d = tgt - loc
    if c.get("ortho") or c["modo"] == "topo":
        ob.rotation_euler = (0, 0, 0)
    elif c.get("pitch") or c["modo"] in ("aereo", "aereo_tarde", "planta_persp"):
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    else:
        yaw = math.atan2(d.y, d.x) - math.pi / 2
        ob.rotation_euler = (math.radians(90), 0, yaw)   # nivelada: verticais retas
    for k, v in c.items():
        if isinstance(v, (int, float, str)):
            ob["cam_" + k] = v
    return ob

def build():
    C = coll("14_Cameras")
    return [make_camera(c, C) for c in CAMS]
