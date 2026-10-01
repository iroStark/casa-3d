"""Utilidades geométricas do gerador da casa (Blender 5.2).

Convenções: metros; origem no cruzamento dos eixos 1/A no piso acabado;
+X leste, +Y norte. Toda geometria é criada por código para ser reproduzível.
"""
import math, os
import bpy, bmesh
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(ROOT, "textures")

# ---------------------------------------------------------------- coleções
def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c

_current = {"coll": None}
def set_coll(c):
    _current["coll"] = c

def link(obj, c=None):
    (c or _current["coll"] or bpy.context.scene.collection).objects.link(obj)
    return obj

# ---------------------------------------------------------------- malhas
def mesh_obj(name, verts, faces, mat=None, c=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        mats = mat if isinstance(mat, (list, tuple)) else [mat]
        for m in mats:
            me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return link(ob, c)

def box(name, x0, x1, y0, y1, z0, z1, mat=None, c=None, bevel=0.0, seg=2, props=None):
    if x0 > x1: x0, x1 = x1, x0
    if y0 > y1: y0, y1 = y1, y0
    if z0 > z1: z0, z1 = z1, z0
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, mat, c)
    if bevel > 0:
        add_bevel(ob, bevel, seg)
    if props:
        for k, val in props.items():
            ob[k] = val
    return ob

def add_bevel(ob, width, seg=2, angle=40):
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.width = width
    m.segments = seg
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    m.use_clamp_overlap = True
    return m

def smooth_angle(ob, deg=35):
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(deg))

def cylinder(name, r, h, loc=(0, 0, 0), seg=32, mat=None, c=None, axis="Z", r2=None, cap=True):
    """Cilindro/cone. loc = centro da base. axis: Z, X ou Y."""
    r2 = r if r2 is None else r2
    verts, faces = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append((r * math.cos(a), r * math.sin(a), 0))
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append((r2 * math.cos(a), r2 * math.sin(a), h))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((i, j, seg + j, seg + i))
    if cap:
        faces.append(tuple(reversed(range(seg))))
        faces.append(tuple(range(seg, 2 * seg)))
    rot = Matrix.Identity(3)
    if axis == "X":
        rot = Matrix.Rotation(math.pi / 2, 3, "Y")
    elif axis == "Y":
        rot = Matrix.Rotation(-math.pi / 2, 3, "X")
    verts = [tuple(rot @ Vector(v) + Vector(loc)) for v in verts]
    ob = mesh_obj(name, verts, faces, mat, c)
    for p in ob.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return ob

def sphere(name, r, loc=(0, 0, 0), seg=24, rings=12, mat=None, c=None, scale=(1, 1, 1)):
    verts, faces = [], []
    for j in range(rings + 1):
        th = math.pi * j / rings
        for i in range(seg):
            ph = 2 * math.pi * i / seg
            verts.append((r * math.sin(th) * math.cos(ph) * scale[0] + loc[0],
                          r * math.sin(th) * math.sin(ph) * scale[1] + loc[1],
                          r * math.cos(th) * scale[2] + loc[2]))
    for j in range(rings):
        for i in range(seg):
            a = j * seg + i; b = j * seg + (i + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    ob = mesh_obj(name, verts, faces, mat, c, smooth=True)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(ob.data); bm.free()
    for p in ob.data.polygons: p.use_smooth = True
    return ob

def torus(name, R, r, loc=(0, 0, 0), seg=32, rseg=12, mat=None, c=None, arc=2 * math.pi):
    verts, faces = [], []
    closed = abs(arc - 2 * math.pi) < 1e-6
    n = seg if closed else seg + 1
    for i in range(n):
        a = arc * i / seg
        for j in range(rseg):
            b = 2 * math.pi * j / rseg
            x = (R + r * math.cos(b)) * math.cos(a)
            y = (R + r * math.cos(b)) * math.sin(a)
            z = r * math.sin(b)
            verts.append((x + loc[0], y + loc[1], z + loc[2]))
    for i in range(seg):
        i2 = (i + 1) % n if closed else i + 1
        for j in range(rseg):
            j2 = (j + 1) % rseg
            faces.append((i * rseg + j, i2 * rseg + j, i2 * rseg + j2, i * rseg + j2))
    return mesh_obj(name, verts, faces, mat, c, smooth=True)

def extrude_profile(name, pts2d, z0, z1, mat=None, c=None):
    """Prisma a partir de um polígono 2D (XY) entre z0 e z1."""
    n = len(pts2d)
    v = [(x, y, z0) for x, y in pts2d] + [(x, y, z1) for x, y in pts2d]
    f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    return mesh_obj(name, v, f, mat, c)

def sweep_profile_x(name, prof_yz, x0, x1, mat=None, c=None):
    """Extruda um perfil no plano YZ ao longo de X (molduras, rodapés)."""
    n = len(prof_yz)
    v = [(x0, y, z) for y, z in prof_yz] + [(x1, y, z) for y, z in prof_yz]
    f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    return mesh_obj(name, v, f, mat, c)

def transform(ob, loc=None, rot_z=0.0, rot=None, scale=None):
    if rot is not None:
        ob.rotation_euler = rot
    elif rot_z:
        ob.rotation_euler = (0, 0, rot_z)
    if loc is not None:
        ob.location = loc
    if scale is not None:
        ob.scale = scale
    return ob

def join(objs, name):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    ctx = bpy.context
    for o in ctx.selected_objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    ctx.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = ctx.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    return ob

def apply_transform(ob):
    me = ob.data
    me.transform(ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)

def group(name, objs, origin=(0, 0, 0), rot_z=0.0, c=None):
    """Agrupa objetos sob um Empty (mantém editável e permite mover o conjunto)."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.3
    link(e, c)
    for o in objs:
        if o is None:
            continue
        o.parent = e
    origin = tuple(origin) + (0.0,) * (3 - len(origin))
    e.location = origin
    e.rotation_euler = (0, 0, rot_z)
    return e

# ---------------------------------------------------------------- UV em escala real
def world_uv(ob, default_m=1.0):
    """Projeção em caixa em coordenadas de mundo: 1 repetição = material['tex_m'] metros.

    Pisos usam (x, y); paredes usam (horizontal, z). Rodada para todos os objetos
    no fim do build, garantindo escala física coerente entre Cycles e glTF.
    """
    if ob.type != "MESH" or len(ob.data.polygons) == 0:
        return
    me = ob.data
    mw = ob.matrix_world
    nmat = mw.to_3x3().inverted().transposed()
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    mats = me.materials
    for p in me.polygons:
        m = mats[p.material_index] if len(mats) > p.material_index else None
        s = float(m.get("tex_m", default_m)) if m else default_m
        rotq = bool(m.get("tex_rot", 0)) if m else False
        n = (nmat @ p.normal).normalized()
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        for li in p.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            if az >= ax and az >= ay:
                u, v = co.x, co.y
            elif ax >= ay:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            if rotq:
                u, v = v, u
            uv[li].uv = (u / s, v / s)

def uv_all(objs=None, skip_prefix=("REF_",)):
    for ob in (objs or bpy.data.objects):
        if ob.name.startswith(skip_prefix):
            continue
        if ob.get("keep_uv"):
            continue
        world_uv(ob)
