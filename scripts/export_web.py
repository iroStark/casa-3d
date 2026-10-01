"""Exporta o modelo web (GLB) derivado do mesmo casa.blend.

blender -b blender/casa.blend -P scripts/export_web.py -- web/public/modelo/casa.glb
- aplica modificadores; remove referências, luzes e câmeras
- 'assa' a multiplicação de cor (nó Mix) nas texturas, pois o glTF não a representa
- une objetos por categoria (WEB_*) para poucas chamadas de desenho; nomes preservados
  para o site: WEB_Cobertura (laje/telhado) e WEB_Forros podem ser ocultados (abrir a cobertura)
- texturas 1024 px em WebP; malhas com Draco
"""
import sys, os, math
import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "web/public/modelo/casa.glb"
TEXDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports", "_tex_web")
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
os.makedirs(TEXDIR, exist_ok=True)
sc = bpy.context.scene

# 1) limpar o que não vai para a web
for ob in list(bpy.data.objects):
    if ob.name.startswith(("REF_", "CAM_", "ALVO_", "CAM_validacao")) or ob.type in ("LIGHT", "CAMERA"):
        bpy.data.objects.remove(ob, do_unlink=True)

# 2) assar tonalização (Mix multiply) e reduzir texturas
def bake_tint(mat):
    nt = mat.node_tree
    if not nt:
        return
    for n in list(nt.nodes):
        if n.type == "MIX" and getattr(n, "blend_type", "") == "MULTIPLY":
            src = None
            for l in nt.links:
                if l.to_node == n and l.from_node.type == "TEX_IMAGE":
                    src = l.from_node
            if not src or not src.image:
                continue
            tint = list(n.inputs[7].default_value)[:3]
            im = src.image
            w, h = im.size
            px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
            px = px.reshape(-1, 4)
            px[:, :3] = np.clip(px[:, :3] * np.array(tint, np.float32), 0, 1)
            nim = bpy.data.images.new(im.name + "_tint_" + mat.name[:10], w, h, alpha=True)
            nim.pixels.foreach_set(px.ravel())
            nim.filepath_raw = os.path.join(TEXDIR, nim.name.replace(" ", "_") + ".png"); nim.file_format = "PNG"; nim.save()
            t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = nim
            p = nt.nodes.get("Principled BSDF")
            nt.links.new(t2.outputs["Color"], p.inputs["Base Color"])
            if src.outputs["Alpha"].links:
                nt.links.new(t2.outputs["Alpha"], p.inputs["Alpha"])
            nt.nodes.remove(n)

for m in bpy.data.materials:
    try:
        bake_tint(m)
    except Exception as e:
        print("tint falhou", m.name, e)

for im in bpy.data.images:
    if im.size[0] > 1024 and im.source == "FILE":
        try:
            im.scale(1024, 1024)
        except Exception as e:
            print("scale falhou", im.name, e)

# 3) aplicar modificadores e unir por categoria
def cat_of(ob):
    names = [c.name for c in ob.users_collection]
    n = ob.name
    if n.startswith(("Laje_", "Cobertura_", "Testeira_")):
        return "WEB_Cobertura"
    if n.startswith(("Forro_", "Sanca_", "LED_sanca", "Viga_eixo2", "Spot_", "Plafon_")) or "03_Estrutura_Vigas" in names:
        return "WEB_Forros"
    if any(c.startswith("01b_") for c in names):
        return "WEB_Piscina"
    if any(c.startswith(("11_",)) for c in names) or "folhas" in n or "foliolos" in n or "copa" in n or "flores" in n:
        return "WEB_Vegetacao"
    if any(c.startswith(("01_", "01c_")) for c in names):
        return "WEB_Entorno"
    if any(c.startswith("09") for c in names) or any(c.startswith("12_") for c in names):
        return "WEB_Interiores"
    if any(c.startswith("04_") for c in names):
        return "WEB_Esquadrias"
    return "WEB_Arquitetura"

dg = bpy.context.evaluated_depsgraph_get()
groups = {}
for ob in list(bpy.data.objects):
    if ob.type != "MESH":
        continue
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
    me.transform(ob.matrix_world)
    groups.setdefault(cat_of(ob), []).append(me)

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
col = bpy.data.collections.new("WEB")
sc.collection.children.link(col)
tris = 0
for gname, meshes in groups.items():
    objs = []
    for me in meshes:
        o = bpy.data.objects.new(me.name, me); col.objects.link(o); objs.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = gname; j.data.name = gname
    bpy.ops.object.select_all(action="DESELECT")
    n = sum(len(p.vertices) - 2 for p in j.data.polygons)
    tris += n
    print(f"  {gname}: {n} triângulos, {len(j.data.materials)} materiais")
print("TRIANGULOS", tris)

# vidros: marcar para o site (substituídos por material transparente leve)
for m in bpy.data.materials:
    p = m.node_tree.nodes.get("Principled BSDF") if m.node_tree else None
    if p and p.inputs["Transmission Weight"].default_value > 0.5:
        m["web_vidro"] = 1

bpy.ops.export_scene.gltf(
    filepath=OUT, export_format="GLB", use_selection=False, export_apply=True,
    export_image_format="WEBP", export_image_quality=80, export_extras=True,
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
    export_draco_position_quantization=14, export_draco_texcoord_quantization=12,
    export_cameras=False, export_lights=False, export_yup=True, export_animations=False)
print("GLB OK", OUT, os.path.getsize(OUT) / 1e6, "MB")
