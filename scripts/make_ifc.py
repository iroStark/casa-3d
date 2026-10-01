"""Gera exports/casa.ifc (IFC4) a partir de data/projeto.json com IfcOpenShell.

.venv/bin/python scripts/make_ifc.py
Não é um BIM executivo: é a base arquitetônica reconstruída (paredes, aberturas,
lajes, pilares, vigas, espaços) com a origem e o status de cada dado em Pset_Reconstrucao.
"""
import json, os, sys
import numpy as np
import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.util.shape  # evita import circular
from ifcopenshell.util.shape_builder import ShapeBuilder

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
D = json.load(open(os.path.join(ROOT, "data", "projeto.json")))

f = api.run("project.create_file", version="IFC4")
proj = api.run("root.create_entity", f, ifc_class="IfcProject", name="Residência unifamiliar — reconstrução")
api.run("unit.assign_unit", f, length={"is_metric": True, "raw": "METERS"}, area={"is_metric": True, "raw": "METERS"}, volume={"is_metric": True, "raw": "METERS"})
model = api.run("context.add_context", f, context_type="Model")
body = api.run("context.add_context", f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model)
site = api.run("root.create_entity", f, ifc_class="IfcSite", name="Lote 30 x 25 m")
bld = api.run("root.create_entity", f, ifc_class="IfcBuilding", name="Residência")
st = api.run("root.create_entity", f, ifc_class="IfcBuildingStorey", name="Térreo (piso acabado 0,00)")
st.Elevation = 0.0
api.run("aggregate.assign_object", f, products=[site], relating_object=proj)
api.run("aggregate.assign_object", f, products=[bld], relating_object=site)
api.run("aggregate.assign_object", f, products=[st], relating_object=bld)
sb = ShapeBuilder(f)

def place(el, x, y, z):
    m = np.eye(4); m[0][3], m[1][3], m[2][3] = x, y, z
    api.run("geometry.edit_object_placement", f, product=el, matrix=m, is_si=True)

def boxrep(dx, dy, dz):
    prof = sb.rectangle(size=(dx, dy))
    ext = sb.extrude(prof, magnitude=dz)
    return sb.get_representation(body, [ext])

def pset(el, props):
    ps = api.run("pset.add_pset", f, product=el, name="Pset_Reconstrucao")
    api.run("pset.edit_pset", f, pset=ps, properties={k: str(v) for k, v in props.items()})

def element(cls, name, x0, x1, y0, y1, z0, z1, props, predefined=None, contain=True):
    el = api.run("root.create_entity", f, ifc_class=cls, name=name, predefined_type=predefined) if predefined else \
        api.run("root.create_entity", f, ifc_class=cls, name=name)
    api.run("geometry.assign_representation", f, product=el, representation=boxrep(x1 - x0, y1 - y0, z1 - z0))
    place(el, x0, y0, z0)
    if contain:
        api.run("spatial.assign_container", f, products=[el], relating_structure=st)
    pset(el, props)
    return el

walls = {}
for w in D["paredes"]["lista"]:
    (x0, x1), (y0, y1) = w["x"], w["y"]
    el = element("IfcWall", w["id"], x0, x1, y0, y1, 0.0, 3.20, {"Fonte": "PDF folhas 01/02", "Status": w["status"], "Espessura_m": round(min(x1 - x0, y1 - y0), 3)})
    walls[w["id"]] = (el, w)

def wall_for(door):
    for wid, (el, w) in walls.items():
        (x0, x1), (y0, y1) = w["x"], w["y"]
        if isinstance(door.get("y"), (int, float)) and isinstance(door.get("x"), list):
            if y0 <= door["y"] <= y1 and door["x"][0] >= x0 - 1e-6 and door["x"][1] <= x1 + 1e-6:
                return el, w
        if isinstance(door.get("x"), (int, float)) and isinstance(door.get("y"), list):
            if x0 <= door["x"] <= x1 and door["y"][0] >= y0 - 1e-6 and door["y"][1] <= y1 + 1e-6:
                return el, w
    return None, None

for d in D["esquadrias"]["portas"]:
    wel, w = wall_for(d)
    if isinstance(d.get("x"), list):
        x0, x1 = d["x"]; t = (w["y"][1] - w["y"][0]) if w else 0.2
        yc = d["y"]; y0, y1 = yc - t / 2, yc + t / 2
    else:
        y0, y1 = d["y"]; t = (w["x"][1] - w["x"][0]) if w else 0.2
        xc = d["x"]; x0, x1 = xc - t / 2, xc + t / 2
    door = element("IfcDoor", d["id"] + " " + d["ambiente"], x0, x1, y0, y1, 0.0, d["altura"],
                   {"Fonte": "PDF folha 02 + cortes", "Status": d["status"], "Largura_m": d["largura"], "Altura_m": d["altura"]}, contain=True)
    door.OverallWidth = d["largura"]; door.OverallHeight = d["altura"]
    if wel is not None:
        op = element("IfcOpeningElement", "Vão " + d["id"], x0, x1, y0 - 0.01 if isinstance(d.get("x"), list) else y0, y1 + 0.01 if isinstance(d.get("x"), list) else y1,
                     0.0, d["altura"], {"Fonte": "vão da porta", "Status": d["status"]}, contain=False)
        if not isinstance(d.get("x"), list):
            pass
        api.run("feature.add_feature", f, feature=op, element=wel)
        api.run("feature.add_filling", f, opening=op, element=door)

for g in D["esquadrias"]["panos_de_vidro"]:
    if isinstance(g["x"], list):
        x0, x1 = g["x"]; y0, y1 = g["y"] - 0.05, g["y"] + 0.05
    else:
        y0, y1 = g["y"]; x0, x1 = g["x"] - 0.05, g["x"] + 0.05
    win = element("IfcWindow", g["id"] + " " + g["ambiente"], x0, x1, y0, y1, g["z"][0], g["z"][1],
                  {"Fonte": "PDF folhas 01/02/03", "Status": g["status"], "Folhas": g["folhas"]})
    win.OverallHeight = g["z"][1] - g["z"][0]
    win.OverallWidth = max(x1 - x0, y1 - y0)
    # verga/viga acima do vão (2,90–3,20)
    element("IfcBeam", "Verga " + g["id"], x0, x1, (y0 + y1) / 2 - 0.10, (y0 + y1) / 2 + 0.10, 2.90, 3.20, {"Fonte": "cortes", "Status": "C seção 20x30"}) \
        if isinstance(g["x"], list) else element("IfcBeam", "Verga " + g["id"], (x0 + x1) / 2 - 0.10, (x0 + x1) / 2 + 0.10, y0, y1, 2.90, 3.20, {"Fonte": "cortes", "Status": "C seção 20x30"})

s = D["laje_cobertura"]
element("IfcSlab", "Laje maciça de cobertura", s["x"][0], s["x"][1], s["y"][0], s["y"][1], 3.20, 3.40,
        {"Fonte": "PDF folhas 03/05", "Status": s["status"], "Caimento": s["caimento"]}, predefined="ROOF")
element("IfcSlab", "Laje de piso (contrapiso)", -0.10, 13.20, -11.25, 0.10, -0.12, -0.02, {"Fonte": "cortes", "Status": "H espessura"}, predefined="FLOOR")

import importlib.util
_spec = importlib.util.spec_from_file_location("estrutura", os.path.join(HERE, "casa", "estrutura.py"))
_m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
COLUMNS, BEAMS = _m.COLUMNS, _m.BEAMS
for nm, x, y, dx, dy in COLUMNS:
    element("IfcColumn", nm, x - dx / 2, x + dx / 2, y - dy / 2, y + dy / 2, 0.0, 3.20, {"Fonte": "PDF folha 01 (fundação)", "Status": "C"})
for nm, x0, x1, y0, y1 in BEAMS:
    element("IfcBeam", nm, x0, x1, y0, y1, 2.90, 3.20, {"Fonte": "PDF folha 01 + cortes", "Status": "C seção / G traçado"})

for a in D["ambientes"]:
    (x0, x1), (y0, y1) = a["x"], a["y"]
    sp = api.run("root.create_entity", f, ifc_class="IfcSpace", name=a["nome"])
    api.run("geometry.assign_representation", f, product=sp, representation=boxrep(x1 - x0, y1 - y0, 3.05))
    place(sp, x0, y0, 0.0)
    api.run("aggregate.assign_object", f, products=[sp], relating_object=st)
    pset(sp, {"Fonte": "PDF folha 02", "Status": a["status"], "Area_aprox_m2": round((x1 - x0) * (y1 - y0), 2)})

p = D["terreno"]["piscina"]
cx, cy = p["centro"]; w, l = p["agua"]
element("IfcBuildingElementProxy", "Piscina 2,50 x 9,50", cx - w / 2, cx + w / 2, cy - l / 2, cy + l / 2, -p["profundidade"] - 0.05, -0.05,
        {"Fonte": "PDF folha 02 (editada)", "Status": p["status"]})

out = os.path.join(ROOT, "exports", "casa.ifc")
os.makedirs(os.path.dirname(out), exist_ok=True)
f.write(out)
print("IFC OK", out, len(f.by_type("IfcWall")), "paredes", len(f.by_type("IfcDoor")), "portas", len(f.by_type("IfcWindow")), "janelas", len(f.by_type("IfcSpace")), "espaços")
