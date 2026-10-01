"""Configuração de render padrão (Cycles + Metal, AgX, denoise OIDN). Versionada no .blend."""
import bpy

def setup(sc, samples=256, res=(3840, 2160)):
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == "METAL")   # só a GPU: CPU+GPU juntos ficam mais lentos no M4
        sc.cycles.device = "GPU"
    except Exception as e:
        print("GPU indisponível:", e)
    c = sc.cycles
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.02
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.denoising_prefilter = "ACCURATE"
    try:
        c.denoising_use_gpu = True
    except Exception:
        pass
    c.max_bounces = 8; c.diffuse_bounces = 4; c.glossy_bounces = 4
    c.transmission_bounces = 8; c.transparent_max_bounces = 12
    c.caustics_reflective = False; c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    c.seed = 612
    c.use_light_tree = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        try:
            sc.view_settings.look = "Medium High Contrast"
        except Exception:
            pass
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False
    sc.render.use_persistent_data = True
