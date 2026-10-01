"""Validação: corte em planta a 1,50 m (ortográfico, 100 px/m) para sobrepor à folha 02.

blender -b blender/casa.blend -P scripts/validate_plan.py -- out.png [z_corte]
"""
import sys, math
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
out = argv[0]
zc = float(argv[1]) if len(argv) > 1 else 1.5
sc = bpy.context.scene
for c in bpy.data.collections:
    if c.name.startswith("00_"):
        c.hide_render = True
cam_d = bpy.data.cameras.new("CAM_validacao")
cam_d.type = "ORTHO"
cam_d.ortho_scale = 16.0
cam_d.clip_start = 0.001
cam_d.clip_end = 50
cam = bpy.data.objects.new("CAM_validacao", cam_d)
sc.collection.objects.link(cam)
cam.location = (6.5, -5.5, zc)
cam.rotation_euler = (0, 0, 0)
sc.camera = cam
sc.render.engine = "BLENDER_WORKBENCH"
sc.render.resolution_x = 1600
sc.render.resolution_y = 1400
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sh = sc.display.shading
sh.light = "FLAT"
sh.color_type = "OBJECT"
for ob in bpy.data.objects:
    n = ob.name
    col = (0.05, 0.05, 0.05, 1)
    if "vidro" in n or "folha" in n or "marco" in n:
        col = (0.1, 0.4, 1.0, 1)
    if n.startswith("PT-"):
        col = (0.9, 0.1, 0.1, 1)
    if n.startswith("Piso") or n.startswith("Rodape") or n.startswith("Terreno") or "soleira" in n:
        col = (1, 1, 1, 0)
        ob.hide_render = True
    ob.color = col
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("VALIDATION RENDER", out)
