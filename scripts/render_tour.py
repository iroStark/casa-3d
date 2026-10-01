"""Renderiza o vídeo do percurso (CAM_PERCURSO) com EEVEE e monta o MP4 com ffmpeg.

blender -b blender/casa.blend -P scripts/render_tour.py -- --res 1920x1080 --samples 48 [--frames 1-1741] [--step 1]
Saída: video/frames/####.png -> video/visita.mp4
"""
import sys, os, time, subprocess
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d=None):
    return argv[argv.index(n) + 1] if n in argv else d

import casa.lighting as lighting

sc = bpy.context.scene
W, H = map(int, arg("--res", "1920x1080").split("x"))
samples = int(arg("--samples", "48"))
out = os.path.join(ROOT, "video", "frames")
os.makedirs(out, exist_ok=True)

ENGINE = arg("--engine", "cycles")
if ENGINE == "cycles":
    import casa.render_setup as rs
    rs.setup(sc, samples=samples, res=(W, H))
    sc.cycles.adaptive_threshold = 0.04
    sc.cycles.use_animated_seed = False   # mesmo padrão de ruído entre quadros (menos cintilação)
sc.render.engine = "BLENDER_EEVEE" if ENGINE == "eevee" else "CYCLES"
ee = sc.eevee
ee.taa_render_samples = samples
ee.use_raytracing = True
try:
    ee.ray_tracing_method = "SCREEN"
    ee.ray_tracing_options.resolution_scale = "2"
    ee.use_fast_gi = True
    ee.fast_gi_method = "GLOBAL_ILLUMINATION"
except Exception as e:
    print("opção EEVEE", e)
ee.use_shadows = True
ee.shadow_ray_count = 2
ee.shadow_step_count = 8
ee.gi_diffuse_bounces = 3
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_depth = "8"
sc.render.use_persistent_data = True
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
for c in bpy.data.collections:
    if c.name.startswith("00_"):
        c.hide_render = True

lighting.world("dia"); lighting.sun("dia")
# luz artificial suave ligada nos interiores (spots a 35%), externas desligadas
for o in (bpy.data.collections["12b_Luzes_Internas"].all_objects):
    if o.type == "LIGHT":
        o.data.energy *= 0.35
for o in (bpy.data.collections["12c_Luzes_Externas"].all_objects):
    o.hide_render = True
for m in bpy.data.materials:
    if m.get("luz"):
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Emission Strength"].default_value *= 0.35
# irradiância: sondas de volume para GI interna no EEVEE
if ENGINE == "eevee" and not bpy.data.objects.get("Sonda_GI_casa"):
    bpy.ops.object.lightprobe_add(type="VOLUME", location=(6.55, -5.6, 1.6))
    pr = bpy.context.active_object; pr.name = "Sonda_GI_casa"
    pr.scale = (7.2, 6.2, 1.65)
    try:
        pr.data.resolution_x, pr.data.resolution_y, pr.data.resolution_z = 22, 18, 6
    except Exception:
        pass
if ENGINE == "eevee":
    try:
        bpy.ops.object.lightprobe_cache_bake(subset="ALL")
    except Exception as e:
        print("bake de sonda:", e)

sc.camera = bpy.data.objects["CAM_PERCURSO"]
fr = arg("--frames")
f0, f1 = (map(int, fr.split("-")) if fr else (sc.frame_start, sc.frame_end))
step = int(arg("--step", "1"))
t0 = time.time()
n = 0
for f in range(f0, f1 + 1, step):
    path = os.path.join(out, f"{f:04d}.png")
    if os.path.exists(path) and "--force" not in argv:
        continue
    sc.frame_set(f)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    n += 1
    if n % 25 == 0:
        el = time.time() - t0
        print(f"QUADRO {f} ({n} feitos) {el/n:.2f}s/quadro", flush=True)
print(f"QUADROS OK {n} em {time.time()-t0:.0f}s")

if "--encode" in argv:
    mp4 = os.path.join(ROOT, "video", "visita.mp4")
    cmd = ["ffmpeg", "-y", "-framerate", str(sc.render.fps), "-start_number", str(f0), "-i", os.path.join(out, "%04d.png"),
           "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4]
    subprocess.run(cmd, check=True)
    print("MP4 OK", mp4)
