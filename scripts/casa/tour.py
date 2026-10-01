"""Percurso da visita (câmera CAM_PERCURSO + alvo animado), compatível com a circulação real.

Pontos: (t[s], posição, alvo, rótulo do ambiente). Altura dos olhos 1,62 m nos interiores.
A rota passa pela porta de entrada PT-01 (aberta), portas PT-03/PT-02 das suítes (abertas)
e sai pela folha de correr aberta do pano JV-03 (sala de jantar -> terraço da piscina).
"""
import json, math, os
import bpy
from mathutils import Vector
from .core import coll, link, ROOT

FPS = 24
EYE = 1.62
WAYPOINTS = [
    (0.0,  (26.0, 10.0, 9.0),     (8.0, -4.0, 1.5),   "Chegada"),
    (5.0,  (20.0, -2.0, 1.65),    (12.0, -4.2, 1.7),  "Chegada"),
    (9.0,  (16.0, -5.35, EYE),    (12.0, -5.35, 1.6), "Entrada"),
    (12.0, (13.9, -5.35, EYE),    (10.0, -5.35, 1.6), "Entrada"),
    (14.5, (11.6, -5.35, EYE),    (9.0, -5.40, 1.6),  "Corredor"),
    (16.5, (10.6, -5.40, EYE),    (10.6, -8.0, 1.5),  "Corredor"),
    (18.5, (10.6, -6.60, EYE),    (12.2, -9.0, 1.2),  "Suíte 1"),
    (21.5, (11.0, -7.60, EYE),    (12.6, -9.3, 1.0),  "Suíte 1"),
    (24.0, (10.6, -6.50, EYE),    (10.6, -4.0, 1.6),  "Suíte 1"),
    (25.5, (10.55, -5.45, EYE),   (8.0, -5.4, 1.6),   "Corredor"),
    (27.0, (8.9, -5.35, EYE),     (7.7, -6.5, 1.6),   "Corredor"),
    (28.5, (7.70, -5.45, EYE),    (7.7, -8.0, 1.5),   "Suíte 2"),
    (30.5, (7.70, -6.70, EYE),    (5.8, -8.3, 1.1),   "Suíte 2"),
    (33.0, (7.62, -7.80, EYE),    (6.0, -9.6, 1.1),   "Suíte 2"),
    (35.5, (7.72, -6.50, EYE),    (7.7, -4.0, 1.6),   "Suíte 2"),
    (36.8, (7.65, -5.45, EYE),    (4.0, -5.6, 1.5),   "Corredor"),
    (38.5, (4.65, -5.40, EYE),    (2.5, -7.5, 1.3),   "Sala de estar"),
    (41.0, (4.70, -6.30, EYE),    (2.0, -8.5, 1.0),   "Sala de estar"),
    (43.0, (4.85, -5.40, EYE),    (2.0, -2.5, 1.3),   "Sala de jantar"),
    (45.0, (5.20, -4.30, EYE),    (4.0, -2.5, 1.0),   "Cozinha"),
    (48.0, (5.20, -2.20, EYE),    (3.0, -2.6, 1.0),   "Cozinha"),
    (50.5, (5.00, -0.95, EYE),    (2.0, -1.5, 1.3),   "Cozinha"),
    (53.5, (2.60, -0.90, EYE),    (0.0, -1.4, 1.5),   "Sala de jantar"),
    (56.5, (0.35, -1.35, EYE),    (-2.0, -1.8, 1.4),  "Saída para a piscina"),
    (59.0, (-1.20, -1.40, EYE),   (-4.0, -4.0, 0.8),  "Piscina"),
    (62.5, (-2.60, -3.00, EYE),   (-5.3, -6.0, 0.0),  "Piscina"),
    (66.5, (-2.90, -8.60, 1.70),  (2.5, -6.0, 1.6),   "Piscina"),
    (72.5, (-2.00, -16.0, 2.40),  (5.0, -5.0, 1.5),   "Despedida"),
]
EXPOSURE = [(0, -0.6), (11.0, -0.6), (13.5, 0.65), (56.0, 0.65), (59.0, -0.4), (72.5, -0.6)]

def catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)

def sample(t):
    """Posição/alvo por Catmull-Rom centrípeto simplificado com tempo reparametrizado suave."""
    W = WAYPOINTS
    if t <= W[0][0]:
        return Vector(W[0][1]), Vector(W[0][2])
    if t >= W[-1][0]:
        return Vector(W[-1][1]), Vector(W[-1][2])
    for i in range(len(W) - 1):
        if W[i][0] <= t <= W[i + 1][0]:
            u = (t - W[i][0]) / (W[i + 1][0] - W[i][0])
            u = u * u * (3 - 2 * u) * 0.35 + u * 0.65   # leve ease nos pontos de parada
            g = lambda k, j: Vector(W[max(0, min(len(W) - 1, k))][j])
            pos = catmull(g(i - 1, 1), g(i, 1), g(i + 1, 1), g(i + 2, 1), u)
            tgt = catmull(g(i - 1, 2), g(i, 2), g(i + 1, 2), g(i + 2, 2), u)
            return pos, tgt
    return Vector(W[-1][1]), Vector(W[-1][2])

def label(t):
    lab = WAYPOINTS[0][3]
    for w in WAYPOINTS:
        if w[0] <= t + 1e-6:
            lab = w[3]
    return lab

def build(step=2):
    sc = bpy.context.scene
    C = coll("14_Cameras")
    cd = bpy.data.cameras.get("CAM_PERCURSO") or bpy.data.cameras.new("CAM_PERCURSO")
    cd.lens = 20; cd.sensor_width = 36; cd.clip_start = 0.05; cd.clip_end = 400
    cam = bpy.data.objects.get("CAM_PERCURSO") or bpy.data.objects.new("CAM_PERCURSO", cd)
    if cam.name not in C.objects:
        link(cam, C)
    tgt = bpy.data.objects.get("ALVO_PERCURSO") or bpy.data.objects.new("ALVO_PERCURSO", None)
    if tgt.name not in C.objects:
        link(tgt, C)
    tgt.empty_display_size = 0.2
    for c in list(cam.constraints):
        cam.constraints.remove(c)
    tr = cam.constraints.new("TRACK_TO"); tr.target = tgt
    tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
    cam.animation_data_clear(); tgt.animation_data_clear()
    end = int(WAYPOINTS[-1][0] * FPS)
    sc.render.fps = FPS
    sc.frame_start = 1; sc.frame_end = end + 1
    for f in range(0, end + 1, step):
        p, q = sample(f / FPS)
        cam.location = p; tgt.location = q
        cam.keyframe_insert("location", frame=f + 1)
        tgt.keyframe_insert("location", frame=f + 1)
    # exposição animada
    vs = sc.view_settings
    for t, e in EXPOSURE:
        vs.exposure = e
        vs.keyframe_insert("exposure", frame=int(t * FPS) + 1)
    cam["nota"] = "Percurso editável: chaves de posição a cada 2 quadros + Empty ALVO_PERCURSO (Track To)"
    return cam, tgt

def export_json(path):
    """Mesmo percurso para o site (coordenadas Blender Z-up, metros)."""
    pts = []
    end = WAYPOINTS[-1][0]
    t = 0.0
    while t <= end + 1e-6:
        p, q = sample(t)
        pts.append({"t": round(t, 3), "p": [round(v, 3) for v in p], "a": [round(v, 3) for v in q], "amb": label(t)})
        t += 0.25
    data = {"fps": FPS, "duracao": end, "waypoints": [{"t": w[0], "p": w[1], "a": w[2], "amb": w[3]} for w in WAYPOINTS],
            "amostras": pts, "exposicao": EXPOSURE}
    json.dump(data, open(path, "w"), ensure_ascii=False)

def validate(min_clear=0.18):
    """Ray cast entre amostras consecutivas (4 cm) + folga lateral: a câmera não atravessa superfícies."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    problems = []
    end = WAYPOINTS[-1][0]
    t = 0.0; dt = 1.0 / FPS
    prev, _ = sample(0)
    hidden_names = ("REF_", "CAM_", "ALVO", "L_")
    while t <= end:
        p, _ = sample(t)
        d = p - prev
        if d.length > 1e-6:
            hit, loc, nor, idx, ob, mat = sc.ray_cast(dg, prev, d.normalized(), distance=d.length + 0.02)
            if hit and not ob.name.startswith(hidden_names):
                problems.append((round(t, 2), "atravessa", ob.name, tuple(round(v, 2) for v in loc)))
        # folga lateral em 8 direções horizontais + cima/baixo
        for k in range(8):
            a = k * math.pi / 4
            v = Vector((math.cos(a), math.sin(a), 0))
            hit, loc, nor, idx, ob, mat = sc.ray_cast(dg, p, v, distance=min_clear)
            if hit and not ob.name.startswith(hidden_names) and "folhas" not in ob.name and "foliolos" not in ob.name:
                problems.append((round(t, 2), "folga<%.2f" % min_clear, ob.name, tuple(round(x, 2) for x in loc)))
                break
        prev = p
        t += dt
    return problems
