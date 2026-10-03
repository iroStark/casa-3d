"""Orquestrador: gera blender/casa.blend do zero (determinístico).

Uso:
  blender -b --factory-startup -P scripts/build.py -- [--stage arch|full] [--out caminho.blend]
"""
import sys, os, importlib, random, time
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default

STAGE = arg("--stage", "full")
OUT = arg("--out", os.path.join(ROOT, "blender", "casa.blend"))
SEED = 20260612  # data da prancha — semente global para tudo que é aleatório
random.seed(SEED)

import casa.estilo as estilo
estilo.ESTILO["nome"] = arg("--estilo", "video")
import casa.core as core
import casa.mats as mats
import casa.arch as arch
for m in (core, mats, arch):
    importlib.reload(m)

t0 = time.time()
# cena limpa
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.name = "Casa"
sc.unit_settings.system = "METRIC"
sc.unit_settings.scale_length = 1.0
sc["semente"] = SEED
sc["estilo"] = estilo.ESTILO["nome"]
sc["fonte"] = "source/projeto.pdf — ver data/projeto.json"

L = mats.lib()
walls = arch.build(L)

if STAGE in ("full", "interior"):
    import casa.site as site; importlib.reload(site)
    import casa.interior as interior; importlib.reload(interior)
    import casa.lighting as lighting; importlib.reload(lighting)
    site.build(L)
    interior.build(L)
    lighting.build(L)
    import casa.cameras as cameras; importlib.reload(cameras)
    cameras.build()
    import casa.tour as tour; importlib.reload(tour)
    tour.build()
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    tour.export_json(os.path.join(ROOT, "data", "percurso.json"))
    import casa.render_setup as rs; importlib.reload(rs)
    rs.setup(sc)

import casa.pranchas as pranchas; importlib.reload(pranchas)
pranchas.build()
import casa.refs as refs; importlib.reload(refs)
refs.build()

bpy.context.view_layer.update()
core.uv_all()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.file.pack_all() if STAGE == "full" and "--pack" in argv else None
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print(f"BUILD OK stage={STAGE} objetos={len(bpy.data.objects)} t={time.time()-t0:.1f}s -> {OUT}")
