"""Gera as texturas próprias do projeto (albedo / rugosidade / normal) com numpy.

Executar: blender -b -P scripts/gen_textures.py
Determinístico: cada textura usa uma semente fixa (SEEDS). Saída em textures/.
Todas as texturas são tileáveis (ruído periódico) e têm escala física anotada em
TEX_SCALE (metros cobertos por 1 repetição) — usada pelo build para os UVs.
"""
import os, sys, math
import numpy as np
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "textures")
os.makedirs(OUT, exist_ok=True)

# -------------------------------------------------------------- utilidades
def rng(seed):
    return np.random.default_rng(seed)

def periodic_noise(n, cells, seed, octaves=1, persistence=0.5):
    """Value-noise periódico (tileável) somado em oitavas, saída 0..1."""
    r = rng(seed)
    acc = np.zeros((n, n), np.float32)
    amp, tot = 1.0, 0.0
    c = cells
    for _ in range(octaves):
        g = r.random((c, c)).astype(np.float32)
        # interpolação bicúbica-suave periódica
        xs = np.arange(n) * c / n
        i0 = np.floor(xs).astype(int) % c
        i1 = (i0 + 1) % c
        f = xs - np.floor(xs)
        f = f * f * (3 - 2 * f)
        a = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
        b = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
        layer = a * (1 - f)[:, None] + b * f[:, None]
        acc += layer * amp
        tot += amp
        amp *= persistence
        c *= 2
    return acc / tot

def stretch_noise(n, cx, cy, seed, octaves=4):
    """Ruído anisotrópico periódico (para veios de madeira)."""
    r = rng(seed)
    acc = np.zeros((n, n), np.float32); amp = 1; tot = 0
    for o in range(octaves):
        gx, gy = cx * 2 ** o, cy * 2 ** o
        g = r.random((gy, gx)).astype(np.float32)
        ys = np.arange(n) * gy / n; xs = np.arange(n) * gx / n
        y0 = np.floor(ys).astype(int) % gy; y1 = (y0 + 1) % gy
        x0 = np.floor(xs).astype(int) % gx; x1 = (x0 + 1) % gx
        fy = ys - np.floor(ys); fx = xs - np.floor(xs)
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx
        b = g[y1][:, x0] * (1 - fx) + g[y1][:, x1] * fx
        acc += (a * (1 - fy)[:, None] + b * fy[:, None]) * amp
        tot += amp; amp *= 0.5
    return acc / tot

def lerp(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return a * (1 - t) + b * t

def srgb(c):
    return np.array(c, np.float32) / 255.0

def save(name, arr, colorspace="sRGB"):
    """arr: HxWx3 ou HxW em 0..1 -> PNG 8 bits."""
    if arr.ndim == 2:
        arr = np.repeat(arr[..., None], 3, axis=2)
    h, w, _ = arr.shape
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = np.clip(arr, 0, 1)
    img = bpy.data.images.new(name, w, h, alpha=False)
    img.colorspace_settings.name = colorspace
    img.pixels.foreach_set(rgba[::-1].ravel())  # Blender: origem embaixo
    img.filepath_raw = os.path.join(OUT, name + ".png")
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print("  tex", name, w, h)

def normal_from_height(hgt, strength=2.0):
    gy, gx = np.gradient(hgt)
    nx = -gx * strength; ny = gy * strength; nz = np.ones_like(hgt)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / l * 0.5 + 0.5, ny / l * 0.5 + 0.5, nz / l * 0.5 + 0.5], -1)

N = 2048

# -------------------------------------------------------------- madeiras
def wood_planks(name, seed, base_dark, base_light, plank_w_px, plank_lengths, scale_m, gaps=True):
    """Assoalho de tábuas corridas. Eixo das tábuas = vertical na imagem."""
    r = rng(seed)
    n = N
    img = np.zeros((n, n, 3), np.float32)
    hgt = np.ones((n, n), np.float32)
    rough = np.zeros((n, n), np.float32)
    cols = n // plank_w_px
    grain_hi = stretch_noise(n, 160, 4, seed + 1, 4)
    grain_lo = stretch_noise(n, 24, 2, seed + 2, 3)
    knots = periodic_noise(n, 24, seed + 3, 2)
    for c in range(cols):
        x0, x1 = c * plank_w_px, (c + 1) * plank_w_px
        y = int(r.random() * n)
        covered = 0
        while covered < n:
            L = min(int(r.choice(plank_lengths)), n - covered)
            tone = r.random()
            shift = r.integers(0, n)
            ys = (np.arange(y, y + L) % n)
            g1 = np.roll(grain_hi, shift, axis=1)[:, x0:x1]
            g2 = np.roll(grain_lo, shift // 2, axis=0)[:, x0:x1]
            # veios: senoide distorcida
            xx = np.arange(x1 - x0)[None, :] / plank_w_px
            v = np.sin((xx * (3 + 4 * tone) + g2[ys] * 2.5) * math.pi * 2) * 0.5 + 0.5
            fine = g1[ys]
            t = 0.25 + 0.4 * tone + 0.22 * v + (fine - 0.5) * 0.35
            seg = lerp(base_dark, base_light, t)
            seg *= (0.92 + 0.1 * tone)
            img[ys, x0:x1] = seg
            rough[ys, x0:x1] = 0.42 + 0.12 * fine + 0.05 * tone
            if gaps:
                hgt[ys[:3], x0:x1] = 0.0
            y += L
            covered += L
        if gaps:
            hgt[:, x0:x0 + 2] = 0.0
    k = np.clip((knots - 0.82) * 6, 0, 1)
    img *= (1 - 0.35 * k)[..., None]
    save(name + "_col", img)
    save(name + "_rgh", rough, "Non-Color")
    save(name + "_nrm", normal_from_height(hgt.astype(np.float32), 3.0), "Non-Color")

def wood_veneer(name, seed, dark, light, scale_rings=7, contrast=1.0):
    """Lâmina de madeira (veio contínuo vertical) para marcenaria."""
    n = 1024
    g = stretch_noise(n, 96, 3, seed, 4)
    g2 = stretch_noise(n, 8, 2, seed + 9, 3)
    xx = np.arange(n)[None, :] / n
    v = np.sin((xx * scale_rings + g2 * 3.0 + g * 0.6) * math.pi * 2) * 0.5 + 0.5
    t = 0.35 + (v - 0.5) * 0.35 * contrast + (g - 0.5) * 0.5
    img = lerp(dark, light, t)
    save(name + "_col", img)
    save(name + "_rgh", 0.35 + 0.15 * g, "Non-Color")

# -------------------------------------------------------------- pedras
def marble(name, seed, base, vein, vein2, n=2048, scale=3.0, sharp=10.0, density=1.0):
    p = periodic_noise(n, 4, seed, 6, 0.55)
    q = periodic_noise(n, 3, seed + 1, 5, 0.5)
    xx, yy = np.meshgrid(np.arange(n) / n, np.arange(n) / n)
    f = np.sin((xx * 1 + yy * 2) * math.pi * 2 * scale / 3 + p * 9 * density + q * 4)
    veins = np.exp(-np.abs(f) * sharp)
    fine = periodic_noise(n, 64, seed + 2, 3)
    cloud = periodic_noise(n, 8, seed + 3, 4)
    img = np.tile(base, (n, n, 1)) * (0.96 + 0.06 * cloud[..., None])
    img = lerp(img, np.tile(vein2, (n, n, 1)), veins * 0.25 + np.clip(fine - 0.7, 0, 1) * 0.3)
    img = lerp(img, np.tile(vein, (n, n, 1)), veins ** 2 * 0.85)
    save(name + "_col", img)
    save(name + "_rgh", 0.12 + 0.08 * fine + 0.05 * veins, "Non-Color")

def stone_tiles(name, seed, base, var, tile_px_w, tile_px_h, joint_col, joint_px=4, pores=True, n=2048):
    """Porcelanato/pedra em placas com junta (travertino / limestone)."""
    r = rng(seed)
    img = np.zeros((n, n, 3), np.float32)
    hgt = np.ones((n, n), np.float32)
    cloud = periodic_noise(n, 6, seed, 5)
    band = stretch_noise(n, 3, 40, seed + 4, 4)
    fine = periodic_noise(n, 128, seed + 5, 2)
    for ty in range(0, n, tile_px_h):
        for tx in range(0, n, tile_px_w):
            tone = r.random()
            sl = (slice(ty, ty + tile_px_h), slice(tx, tx + tile_px_w))
            t = 0.3 + 0.4 * tone + (cloud[sl] - 0.5) * 0.8 + (np.roll(band, int(r.random() * n), 1)[sl] - 0.5) * 0.6
            hh, ww = t.shape
            img[sl] = lerp(np.tile(base, (hh, ww, 1)), np.tile(var, (hh, ww, 1)), t)
    if pores:
        pr = (fine < 0.18).astype(np.float32)
        img *= (1 - 0.18 * pr)[..., None]
        hgt -= 0.3 * pr
    for ty in range(0, n, tile_px_h):
        img[ty:ty + joint_px] = joint_col; hgt[ty:ty + joint_px] = 0
    for tx in range(0, n, tile_px_w):
        img[:, tx:tx + joint_px] = joint_col; hgt[:, tx:tx + joint_px] = 0
    save(name + "_col", img)
    save(name + "_rgh", 0.35 + 0.25 * fine, "Non-Color")
    save(name + "_nrm", normal_from_height(hgt, 2.5), "Non-Color")

def plaster(name, seed, base, amp=0.04, n=1024):
    c = periodic_noise(n, 8, seed, 6, 0.6)
    f = periodic_noise(n, 96, seed + 1, 2)
    img = np.tile(base, (n, n, 1)) * (1 - amp + 2 * amp * c[..., None]) * (0.985 + 0.03 * f[..., None])
    save(name + "_col", img)
    save(name + "_nrm", normal_from_height(c * 0.6 + f * 0.4, 1.2), "Non-Color")

def concrete(name, seed, base, n=2048):
    c = periodic_noise(n, 6, seed, 6, 0.6)
    f = periodic_noise(n, 160, seed + 1, 2)
    spots = (periodic_noise(n, 200, seed + 2, 1) < 0.08).astype(np.float32)
    img = np.tile(base, (n, n, 1)) * (0.85 + 0.25 * c[..., None]) * (0.96 + 0.06 * f[..., None])
    img *= (1 - 0.25 * spots)[..., None]
    save(name + "_col", img)
    save(name + "_rgh", 0.55 + 0.25 * c, "Non-Color")

# -------------------------------------------------------------- tecidos
def fabric(name, seed, base, var, weave_px=6, n=1024, slub=0.5):
    xx, yy = np.meshgrid(np.arange(n), np.arange(n))
    warp = (np.sin(xx * math.pi * 2 / weave_px) * 0.5 + 0.5)
    weft = (np.sin(yy * math.pi * 2 / weave_px) * 0.5 + 0.5)
    check = ((xx // weave_px + yy // weave_px) % 2).astype(np.float32)
    w = warp * check + weft * (1 - check)
    s = stretch_noise(n, 64, 4, seed, 3)
    c = periodic_noise(n, 8, seed + 1, 3)
    t = 0.5 + (w - 0.5) * 0.5 + (s - 0.5) * slub + (c - 0.5) * 0.3
    img = lerp(np.tile(base, (n, n, 1)), np.tile(var, (n, n, 1)), t)
    save(name + "_col", img)
    save(name + "_nrm", normal_from_height(w * 0.7 + s * 0.3, 1.5), "Non-Color")

def boucle(name, seed, base, n=1024):
    f = periodic_noise(n, 180, seed, 3, 0.6)
    c = periodic_noise(n, 10, seed + 1, 3)
    loops = np.clip((f - 0.45) * 3, 0, 1)
    img = np.tile(base, (n, n, 1)) * (0.82 + 0.25 * loops[..., None]) * (0.97 + 0.05 * c[..., None])
    save(name + "_col", img)
    save(name + "_nrm", normal_from_height(f, 4.0), "Non-Color")

def rug(name, seed, base, accent, border, n=2048, pattern="classic"):
    xx, yy = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n))
    wool = periodic_noise(n, 300, seed, 2)
    cloud = periodic_noise(n, 6, seed + 1, 4)
    img = np.tile(base, (n, n, 1)) * (0.9 + 0.15 * cloud[..., None])
    d = np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy))
    if pattern == "classic":
        bd = ((d > 0.035) & (d < 0.075)) | ((d > 0.09) & (d < 0.1))
        img[bd] = img[bd] * 0 + border
        # medalhão suave e grade de losangos esmaecida
        u = (xx - 0.5) * 2; v = (yy - 0.5) * 2
        diamond = (np.abs(np.sin((u + v) * 14)) < 0.05) | (np.abs(np.sin((u - v) * 14)) < 0.05)
        inner = d > 0.12
        img[diamond & inner] = img[diamond & inner] * 0.6 + accent * 0.4
        med = (np.abs(u) * 0.9 + np.abs(v) * 1.3) < 0.35
        img[med] = img[med] * 0.55 + accent * 0.45
    else:  # listras tonais
        stripes = (np.sin(yy * 60) > 0.6) & (d > 0.03)
        img[stripes] = img[stripes] * 0.75 + accent * 0.25
    img *= (0.9 + 0.15 * wool[..., None])
    save(name + "_col", img)

# -------------------------------------------------------------- outros
def pool_tiles(name, seed, n=1024):
    r = rng(seed)
    t = 32  # pastilha 2,5 cm em 0,8 m
    img = np.zeros((n, n, 3), np.float32)
    base = srgb((110, 178, 180)); var = srgb((70, 140, 150))
    for y in range(0, n, t):
        for x in range(0, n, t):
            img[y:y + t, x:x + t] = lerp(base[None, None], var[None, None], np.array([[r.random()]]))
    img[::t] = srgb((225, 225, 220)); img[:, ::t] = srgb((225, 225, 220))
    img[1::t] = srgb((225, 225, 220)); img[:, 1::t] = srgb((225, 225, 220))
    save(name + "_col", img)

def grass(name, seed, n=2048):
    f = periodic_noise(n, 256, seed, 3)
    c = periodic_noise(n, 8, seed + 1, 5)
    d = periodic_noise(n, 30, seed + 2, 3)
    a = srgb((58, 92, 38)); b = srgb((112, 140, 60)); dry = srgb((150, 140, 85))
    img = lerp(np.tile(a, (n, n, 1)), np.tile(b, (n, n, 1)), f * 0.7 + c * 0.5 - 0.1)
    img = lerp(img, np.tile(dry, (n, n, 1)), np.clip((d - 0.7) * 2, 0, 0.4))
    save(name + "_col", img)

def leaf_atlas(name, seed, n=2048):
    """Atlas RGBA 4x4: 8 folhas lanceoladas isoladas + 8 raminhos com 5–9 folhas pequenas."""
    r = rng(seed)
    rgba = np.zeros((n, n, 4), np.float32)
    cell = n // 4
    def leaf(canvas, cx, cy, L, W, ang, col):
        # folha lanceolada com ponta, nervura central e laterais
        h, w = canvas.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        ca, sa = math.cos(ang), math.sin(ang)
        u = ((xx - cx) * ca + (yy - cy) * sa) / L          # ao longo da folha (0 base .. 1 ponta)
        v = (-(xx - cx) * sa + (yy - cy) * ca) / W
        prof = np.clip(np.sin(np.clip(u, 0, 1) * math.pi) ** 0.75 * (1 - 0.35 * u), 0, 1)
        m = (u > 0) & (u < 1) & (np.abs(v) < prof)
        nerv = (np.abs(v) < 0.045) & m
        lat = (np.abs(np.sin((u * 9 - np.abs(v) * 2.2) * math.pi)) < 0.12) & m & (np.abs(v) < prof * 0.85)
        shade = 0.82 + 0.25 * (1 - np.abs(v)) - 0.12 * u
        c = np.array(col, np.float32)
        canvas[m, :3] = (c[None] * shade[m][:, None])
        canvas[lat, :3] *= 1.12
        canvas[nerv, :3] = canvas[nerv, :3] * 0.6 + np.array([0.55, 0.62, 0.35]) * 0.4
        canvas[m, 3] = 1.0
    for i in range(16):
        cy_, cx_ = divmod(i, 4)
        tile = np.zeros((cell, cell, 4), np.float32)
        hue = r.random()
        base = np.array([0.10 + 0.08 * hue, 0.22 + 0.12 * r.random(), 0.06 + 0.05 * r.random()])
        if i < 8:
            leaf(tile, cell * 0.5, cell * 0.96, cell * 0.92, cell * 0.20 * (0.7 + 0.5 * r.random()), -math.pi / 2, base)
        else:
            # raminho: haste fina + folhas alternadas
            yy, xx = np.mgrid[0:cell, 0:cell]
            stem = (np.abs(xx - cell * 0.5) < 2) & (yy > cell * 0.1)
            tile[stem, :3] = [0.25, 0.2, 0.12]; tile[stem, 3] = 1
            k = r.integers(5, 10)
            for j in range(k):
                t = 0.15 + 0.8 * j / k
                side = 1 if j % 2 else -1
                ang = -math.pi / 2 + side * (0.6 + 0.4 * r.random())
                col = base * (0.85 + 0.35 * r.random())
                leaf(tile, cell * 0.5, cell * (1 - t * 0.9), cell * 0.38, cell * 0.09, ang, col)
            leaf(tile, cell * 0.5, cell * 0.14, cell * 0.14, cell * 0.06, -math.pi / 2, base)
        rgba[cy_ * cell:(cy_ + 1) * cell, cx_ * cell:(cx_ + 1) * cell] = tile
    img = bpy.data.images.new(name + "_col", n, n, alpha=True)
    img.pixels.foreach_set(rgba[::-1].ravel())
    img.filepath_raw = os.path.join(OUT, name + "_col.png"); img.file_format = "PNG"
    img.alpha_mode = "STRAIGHT"
    img.save(); bpy.data.images.remove(img)
    print("  tex", name)

def art(name, seed, palette, n=1024, kind="abstract"):
    r = rng(seed)
    img = np.tile(srgb((236, 228, 214)), (n, n, 1))
    xx, yy = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n))
    if kind == "abstract":
        for k in range(5):
            cx, cy, rad = r.random(), r.random(), 0.15 + 0.3 * r.random()
            m = ((xx - cx) ** 2 + (yy - cy) ** 2) < rad ** 2
            col = srgb(palette[k % len(palette)])
            img[m] = img[m] * 0.25 + col * 0.75
        tex = periodic_noise(n, 100, seed, 2)
        img *= (0.95 + 0.08 * tex[..., None])
    elif kind == "botanical":
        for k in range(9):
            a = r.random() * math.pi
            x0, y0 = 0.5 + (r.random() - 0.5) * 0.3, 0.85
            for s in np.linspace(0, 1, 120):
                px = x0 + math.cos(a) * s * 0.35 * (r.random() * 0.1 + 0.95)
                py = y0 - math.sin(a) * s * 0.6
                m = ((xx - px) ** 2 + (yy - py) ** 2) < (0.012 * (1 - s) + 0.003) ** 2
                img[m] = srgb(palette[k % len(palette)])
    elif kind == "lines":
        for k in range(12):
            y = r.random()
            m = np.abs(yy - y - 0.05 * np.sin(xx * 6 + k)) < 0.004
            img[m] = srgb(palette[k % len(palette)])
    save(name + "_col", img)

SEEDS = {}
def main():
    print("Gerando texturas em", OUT)
    if "--so-folhas" in sys.argv:
        leaf_atlas("leaves", 93); return
    # Carvalho natural claro-mel (piso social e íntimo): tábuas 20 cm, 2048 px = 2,40 m
    wood_planks("oak_floor", 11, srgb((150, 104, 64)), srgb((206, 162, 110)), 256, [1000, 1300, 1600], 1.6)
    # Cumaru (deck da piscina): réguas 14 cm, 2048 px = 2,0 m
    wood_planks("deck", 12, srgb((96, 58, 34)), srgb((150, 98, 60)), 128, [900, 1300, 1700], 2.24)
    wood_veneer("oak_veneer", 13, srgb((168, 122, 78)), srgb((214, 172, 122)))
    wood_veneer("walnut", 14, srgb((70, 44, 28)), srgb((122, 82, 52)), 9)
    wood_veneer("freijo", 15, srgb((140, 98, 58)), srgb((190, 146, 96)), 6)
    marble("calacatta", 21, srgb((240, 237, 231)), srgb((150, 140, 128)), srgb((200, 180, 150)), sharp=6)
    marble("travertine_slab", 22, srgb((222, 205, 178)), srgb((190, 170, 140)), srgb((205, 186, 158)), scale=8, sharp=4, density=0.4)
    marble("verde_stone", 23, srgb((54, 74, 64)), srgb((210, 214, 200)), srgb((80, 100, 88)), sharp=14)
    # Travertino/limestone 60x120 em 2,4 m -> placa 512x1024 px
    stone_tiles("limestone_floor", 31, srgb((226, 214, 192)), srgb((206, 190, 164)), 512, 1024, srgb((190, 180, 165)), 3)
    # Porcelanato dos banhos 60x120 bege-areia
    stone_tiles("porcelain_bath", 32, srgb((232, 224, 210)), srgb((214, 202, 184)), 512, 1024, srgb((200, 195, 185)), 3, pores=False)
    # Revestimento de parede do box: 30x60 (zellige-like suave) em 1,2 m
    stone_tiles("bath_wall", 33, srgb((236, 230, 220)), srgb((214, 206, 194)), 512, 1024, srgb((215, 210, 200)), 4, pores=False)
    # Pedra do terraço/passeio 80x80 em 2,4 m
    stone_tiles("terrace_stone", 34, srgb((205, 196, 180)), srgb((180, 170, 152)), 512, 512, srgb((150, 145, 135)), 5)
    stone_tiles("coping", 35, srgb((232, 222, 204)), srgb((214, 202, 182)), 1024, 512, srgb((190, 182, 170)), 4)
    plaster("plaster_warm", 41, srgb((236, 230, 220)))
    plaster("plaster_ext", 42, srgb((228, 220, 206)), 0.07)
    plaster("plaster_rose", 43, srgb((214, 170, 152)), 0.035)
    plaster("plaster_sage", 44, srgb((178, 182, 160)), 0.035)
    concrete("concrete_garage", 51, srgb((150, 148, 142)))
    concrete("concrete_drive", 52, srgb((176, 170, 160)))
    fabric("linen_natural", 61, srgb((214, 202, 182)), srgb((190, 176, 152)))
    fabric("linen_white", 62, srgb((242, 238, 230)), srgb((222, 216, 206)), 4, slub=0.25)
    fabric("velvet_olive", 63, srgb((102, 108, 72)), srgb((80, 86, 56)), 3, slub=0.15)
    fabric("wool_charcoal", 64, srgb((78, 80, 84)), srgb((60, 62, 66)), 5)
    fabric("linen_rose", 65, srgb((214, 168, 150)), srgb((196, 150, 132)), 5)
    fabric("cotton_sand", 66, srgb((198, 176, 144)), srgb((176, 154, 122)), 4, slub=0.2)
    boucle("boucle_cream", 71, srgb((232, 224, 208)))
    rug("rug_living", 81, srgb((214, 200, 176)), srgb((140, 110, 80)), srgb((150, 120, 92)))
    rug("rug_bed", 82, srgb((226, 212, 192)), srgb((190, 160, 140)), srgb((170, 140, 120)), pattern="stripes")
    rug("rug_dining", 83, srgb((200, 188, 168)), srgb((120, 104, 84)), srgb((130, 112, 90)), pattern="stripes")
    pool_tiles("pool_tiles", 91)
    grass("grass", 92)
    leaf_atlas("leaves", 93)
    art("art_a", 101, [(176, 120, 86), (214, 180, 140), (110, 120, 96), (60, 70, 70)])
    art("art_b", 102, [(110, 128, 100), (90, 104, 80), (160, 170, 140)], kind="botanical")
    art("art_c", 103, [(150, 110, 80), (60, 60, 60), (190, 150, 110)], kind="lines")
    art("art_d", 104, [(200, 150, 130), (230, 200, 170), (150, 110, 90), (120, 90, 80)])
    print("OK")

main()
