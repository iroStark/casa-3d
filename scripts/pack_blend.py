import bpy, os
bpy.ops.file.make_paths_relative()
bpy.ops.file.pack_all()
out = os.path.abspath("exports/casa_empacotado.blend")
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, copy=True)
print("PACK OK", out, os.path.getsize(out)/1e6)
