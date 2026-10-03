"""Biblioteca de materiais PBR (Principled BSDF + texturas próprias em textures/).

Cada material guarda 'tex_m' (metros por repetição) usado pelo UV em escala real,
e 'categoria' (arquitetura | acabamento | proposta) para rastreabilidade.
Os nós ficam simples (imagem -> Principled) para exportar corretamente em glTF.
"""
import os
import bpy
from .core import TEX

_cache = {}

def _img(name, colorspace="sRGB"):
    path = os.path.join(TEX, name + ".png")
    if not os.path.exists(path):
        return None
    key = os.path.basename(path)
    im = bpy.data.images.get(key)
    if im is None:
        im = bpy.data.images.load(path)
        im.name = key
    im.colorspace_settings.name = colorspace
    return im

def pbr(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, tex=None, tex_m=1.0,
        normal=None, nstrength=0.4, rough_tex=None, transmission=0.0, ior=1.45,
        alpha=1.0, emission=None, estrength=0.0, coat=0.0, sheen=0.0, subsurface=0.0,
        tint=None, categoria="acabamento", tex_rot=False, alpha_tex=False, thin=False,
        spec=0.5):
    if name in _cache:
        return _cache[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    out = nt.nodes.get("Material Output")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["IOR"].default_value = ior
    p.inputs["Specular IOR Level"].default_value = spec
    if transmission:
        p.inputs["Transmission Weight"].default_value = transmission
    if coat:
        p.inputs["Coat Weight"].default_value = coat
        p.inputs["Coat Roughness"].default_value = 0.08
    if sheen:
        p.inputs["Sheen Weight"].default_value = sheen
    if subsurface:
        p.inputs["Subsurface Weight"].default_value = subsurface
    if thin:
        p.inputs["Thin Wall"].default_value = True
    if emission is not None:
        p.inputs["Emission Color"].default_value = (*emission, 1)
        p.inputs["Emission Strength"].default_value = estrength
    y = 300
    if tex:
        im = _img(tex)
        if im:
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; t.location = (-600, y)
            t.interpolation = "Cubic"
            if tint is not None:
                mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
                mix.location = (-300, y)
                mix.inputs["Factor"].default_value = 1.0
                nt.links.new(t.outputs["Color"], mix.inputs[6])
                mix.inputs[7].default_value = (*tint, 1)
                nt.links.new(mix.outputs[2], p.inputs["Base Color"])
            else:
                nt.links.new(t.outputs["Color"], p.inputs["Base Color"])
            if alpha_tex:
                nt.links.new(t.outputs["Alpha"], p.inputs["Alpha"])
    if rough_tex:
        im = _img(rough_tex, "Non-Color")
        if im:
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; t.location = (-600, 0)
            nt.links.new(t.outputs["Color"], p.inputs["Roughness"])
    if normal:
        im = _img(normal, "Non-Color")
        if im:
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; t.location = (-600, -300)
            nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-300, -300)
            nm.inputs["Strength"].default_value = nstrength
            nt.links.new(t.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
    if alpha < 1.0 or alpha_tex:
        p.inputs["Alpha"].default_value = alpha if not alpha_tex else 1.0
        try:
            m.surface_render_method = "DITHERED"
        except Exception:
            pass
    m.diffuse_color = (*color, 1)
    m["tex_m"] = tex_m
    m["tex_rot"] = 1 if tex_rot else 0
    m["categoria"] = categoria
    _cache[name] = m
    return m

def emission(name, color=(1.0, 0.85, 0.65), strength=10.0):
    if name in _cache:
        return _cache[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Emission Color"].default_value = (*color, 1)
    p.inputs["Emission Strength"].default_value = strength
    p.inputs["Roughness"].default_value = 0.6
    m["tex_m"] = 1.0
    m["categoria"] = "iluminacao"
    m["luz"] = 1
    _cache[name] = m
    return m

def shadow_transparent(m):
    """Vidro/água: aparência de vidro para a câmera, transparente para sombras e raios difusos
    (técnica usual de archviz — deixa o sol entrar e converge muito mais rápido no Cycles)."""
    nt = m.node_tree
    p = nt.nodes.get("Principled BSDF"); out = nt.nodes.get("Material Output")
    lp = nt.nodes.new("ShaderNodeLightPath"); lp.location = (-200, 500)
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; mx.location = (0, 500)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.location = (0, 350)
    ms = nt.nodes.new("ShaderNodeMixShader"); ms.location = (250, 400)
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
    nt.links.new(lp.outputs["Is Diffuse Ray"], mx.inputs[1])
    nt.links.new(mx.outputs[0], ms.inputs[0])
    nt.links.new(p.outputs["BSDF"], ms.inputs[1])
    nt.links.new(tr.outputs["BSDF"], ms.inputs[2])
    out.target = "CYCLES"
    nt.links.new(ms.outputs["Shader"], out.inputs["Surface"])
    # saída separada para EEVEE/glTF continua sendo o Principled
    out2 = nt.nodes.new("ShaderNodeOutputMaterial"); out2.target = "EEVEE"; out2.location = (450, 150)
    nt.links.new(p.outputs["BSDF"], out2.inputs["Surface"])
    m["sombra_transparente"] = 1
    return m

def glass(name="Vidro", tint=(0.92, 0.96, 0.95), rough=0.0):
    if name in _cache:
        return _cache[name]
    m = pbr(name, color=tint, rough=rough, transmission=1.0, ior=1.5, categoria="arquitetura", thin=True)
    try:
        m.surface_render_method = "BLENDED"
        m.use_transparent_shadow = True
    except Exception:
        pass
    shadow_transparent(m)
    return m

def lib():
    """Paleta do projeto. Retorna dict nome->material."""
    L = {}
    A = "arquitetura"; P = "proposta"
    # ---- arquitetura / acabamentos de base
    L["parede_int"] = pbr("Pintura interna — cinza-claro (vídeo)", (0.82, 0.82, 0.8), 0.85, tex="plaster_gray_col", tex_m=2.0, normal="plaster_gray_nrm", nstrength=0.12)
    L["parede_ext"] = pbr("Reboco externo texturizado — greige", (0.8, 0.76, 0.7), 0.9, tex="plaster_greige_col", tex_m=2.0, normal="plaster_greige_nrm", nstrength=0.35, categoria=A)
    L["parede_rosa"] = pbr("Pintura rosé (suite 2)", (0.78, 0.6, 0.53), 0.85, tex="plaster_rose_col", tex_m=2.0, normal="plaster_warm_nrm", nstrength=0.15, categoria=P)
    L["parede_salvia"] = pbr("Pintura verde-sálvia (suite 1)", (0.62, 0.64, 0.55), 0.85, tex="plaster_sage_col", tex_m=2.0, normal="plaster_warm_nrm", nstrength=0.15, categoria=P)
    L["forro"] = pbr("Forro de gesso — branco", (0.9, 0.89, 0.86), 0.9, categoria=A)
    L["laje"] = pbr("Concreto da laje (face aparente)", (0.62, 0.61, 0.58), 0.85, tex="concrete_garage_col", tex_m=3.0, categoria=A)
    L["impermeab"] = pbr("Manta/impermeabilização da laje (cinza claro)", (0.7, 0.69, 0.66), 0.9, tex="concrete_drive_col", tex_m=3.0, categoria=A, tint=(0.95, 0.94, 0.92))
    L["piso_madeira"] = pbr("Porcelanato amadeirado claro 20x120", (0.8, 0.7, 0.58), 0.38, tex="oak_light_col", tex_m=1.6, rough_tex="oak_light_rgh", normal="oak_light_nrm", nstrength=0.25, coat=0.1)
    L["piso_banho"] = pbr("Porcelanato areia 60x120 (banhos)", (0.88, 0.85, 0.8), 0.3, tex="porcelain_bath_col", tex_m=2.4, rough_tex="porcelain_bath_rgh", normal="porcelain_bath_nrm", nstrength=0.2)
    L["parede_banho"] = pbr("Revestimento 30x60 off-white (box)", (0.9, 0.88, 0.84), 0.2, tex="bath_wall_col", tex_m=1.2, normal="bath_wall_nrm", nstrength=0.25, coat=0.3)
    L["piso_externo"] = pbr("Pedra calcária 80x80 (terraço)", (0.78, 0.74, 0.68), 0.75, tex="terrace_stone_col", tex_m=3.2, rough_tex="terrace_stone_rgh", normal="terrace_stone_nrm", nstrength=0.5)
    L["piso_garagem"] = pbr("Piso de concreto polido (garagem)", (0.58, 0.57, 0.55), 0.45, tex="concrete_garage_col", tex_m=3.0, rough_tex="concrete_garage_rgh")
    L["calcada"] = pbr("Concreto desempenado (acesso)", (0.68, 0.66, 0.62), 0.8, tex="concrete_drive_col", tex_m=3.0, rough_tex="concrete_drive_rgh")
    L["borda_piscina"] = pbr("Borda de pedra (piscina)", (0.88, 0.84, 0.78), 0.7, tex="coping_col", tex_m=2.0, rough_tex="coping_rgh", normal="coping_nrm", nstrength=0.4)
    L["deck"] = pbr("Deck de madeira clara", (0.72, 0.62, 0.55), 0.6, tex="deck_gray_col", tex_m=2.24, tint=(1.18, 1.1, 1.08), rough_tex="deck_gray_rgh", normal="deck_gray_nrm", nstrength=0.6, categoria=P)
    L["pastilha"] = pbr("Pastilha de vidro (piscina)", (0.42, 0.68, 0.7), 0.2, tex="pool_tiles_aqua_col", tex_m=0.8, coat=0.4)
    L["agua"] = shadow_transparent(pbr("Água", (0.6, 0.93, 0.98), 0.02, transmission=1.0, ior=1.333, categoria="paisagismo"))
    L["grama"] = pbr("Gramado (esmeralda)", (0.25, 0.4, 0.15), 0.95, tex="grass_col", tex_m=2.0, tint=(0.72, 0.74, 0.62), categoria="paisagismo")
    L["terra"] = pbr("Terra/casca de pinus (canteiros)", (0.24, 0.17, 0.12), 0.95, tex="concrete_drive_col", tex_m=1.0, tint=(0.38, 0.27, 0.19), categoria="paisagismo")
    L["vidro"] = glass("Vidro incolor 8 mm")
    L["vidro_box"] = glass("Vidro do box", (0.95, 0.97, 0.97))
    L["vidro_fosco"] = pbr("Vidro jateado", (0.95, 0.95, 0.94), 0.35, transmission=1.0, categoria="proposta")
    L["alu_bronze"] = pbr("Alumínio preto (caixilhos)", (0.03, 0.03, 0.032), 0.4, 0.7, categoria=A)
    L["alu_preto"] = pbr("Alumínio preto fosco", (0.03, 0.03, 0.03), 0.45, 0.8)
    L["latao"] = pbr("Latão escovado", (0.78, 0.6, 0.36), 0.28, 1.0)
    L["inox"] = pbr("Inox escovado", (0.74, 0.74, 0.72), 0.25, 1.0)
    L["cromado"] = pbr("Metal cromado", (0.9, 0.9, 0.9), 0.06, 1.0)
    L["ferro"] = pbr("Ferro pintado grafite", (0.07, 0.07, 0.07), 0.5, 0.6)
    L["porcelana"] = pbr("Louça sanitária branca", (0.93, 0.93, 0.91), 0.08, coat=0.5)
    L["laca_branca"] = pbr("Laca branca acetinada", (0.88, 0.86, 0.82), 0.35)
    L["laca_off"] = pbr("Laca off-white (boiserie)", (0.86, 0.83, 0.78), 0.55)
    L["porta_madeira"] = pbr("Freijó natural (portas)", (0.55, 0.38, 0.23), 0.45, tex="freijo_col", tex_m=1.2, rough_tex="freijo_rgh", categoria=A)
    L["carvalho"] = pbr("Lâmina de carvalho (marcenaria)", (0.65, 0.48, 0.32), 0.42, tex="oak_veneer_col", tex_m=1.0, rough_tex="oak_veneer_rgh")
    L["nogueira"] = pbr("Nogueira (móveis)", (0.3, 0.19, 0.12), 0.38, tex="walnut_col", tex_m=1.0, rough_tex="walnut_rgh", coat=0.2)
    L["calacatta"] = pbr("Pedra cinza (ilha)", (0.7, 0.69, 0.66), 0.25, tex="pedra_cinza_col", tex_m=1.6, rough_tex="pedra_cinza_rgh", coat=0.2)
    L["travertino"] = pbr("Travertino romano", (0.86, 0.8, 0.7), 0.35, tex="travertine_slab_col", tex_m=1.5, rough_tex="travertine_slab_rgh")
    L["pedra_verde"] = pbr("Pedra verde (lavabo)", (0.2, 0.28, 0.24), 0.2, tex="verde_stone_col", tex_m=1.2, rough_tex="verde_stone_rgh", coat=0.3)
    # ---- tecidos e decoração (proposta)
    L["linho"] = pbr("Linho natural", (0.82, 0.77, 0.69), 0.85, tex="linen_natural_col", tex_m=0.5, normal="linen_natural_nrm", nstrength=0.3, sheen=0.4, categoria=P)
    L["linho_branco"] = pbr("Linho branco", (0.94, 0.92, 0.88), 0.85, tex="linen_white_col", tex_m=0.4, normal="linen_white_nrm", nstrength=0.25, sheen=0.4, categoria=P)
    L["voil"] = pbr("Voil de linho (cortina)", (0.95, 0.93, 0.89), 0.8, tex="linen_white_col", tex_m=0.6, transmission=0.0, subsurface=0.0, alpha=0.62, sheen=0.3, categoria=P)
    L["blackout"] = pbr("Cortina de linho areia", (0.76, 0.69, 0.58), 0.85, tex="cotton_sand_col", tex_m=0.6, sheen=0.4, categoria=P)
    L["veludo_oliva"] = pbr("Veludo oliva", (0.38, 0.4, 0.26), 0.6, tex="velvet_olive_col", tex_m=0.4, sheen=1.0, categoria=P)
    L["la_grafite"] = pbr("Lã grafite", (0.3, 0.3, 0.32), 0.85, tex="wool_charcoal_col", tex_m=0.4, sheen=0.5, categoria=P)
    L["linho_rosa"] = pbr("Linho rosé", (0.8, 0.63, 0.56), 0.85, tex="linen_rose_col", tex_m=0.4, sheen=0.4, categoria=P)
    L["algodao_areia"] = pbr("Algodão areia", (0.74, 0.65, 0.53), 0.85, tex="cotton_sand_col", tex_m=0.4, sheen=0.4, categoria=P)
    L["boucle"] = pbr("Bouclé creme", (0.9, 0.86, 0.79), 0.95, tex="boucle_cream_col", tex_m=0.3, normal="boucle_cream_nrm", nstrength=0.6, sheen=0.5, categoria=P)
    L["couro"] = pbr("Couro caramelo", (0.45, 0.25, 0.12), 0.45, coat=0.2, categoria=P)
    L["tapete_sala"] = pbr("Tapete de lã (sala)", (0.8, 0.75, 0.66), 0.95, tex="rug_living_col", tex_m=1.0, sheen=0.6, categoria=P)
    L["tapete_quarto"] = pbr("Tapete de lã (quartos)", (0.85, 0.8, 0.72), 0.95, tex="rug_bed_col", tex_m=1.0, sheen=0.6, categoria=P)
    L["tapete_jantar"] = pbr("Tapete de sisal (jantar)", (0.75, 0.7, 0.62), 0.95, tex="rug_dining_col", tex_m=1.0, sheen=0.3, categoria=P)
    L["palha"] = pbr("Palhinha natural", (0.78, 0.66, 0.45), 0.7, categoria=P)
    L["ceramica_terracota"] = pbr("Cerâmica terracota", (0.6, 0.36, 0.24), 0.75, categoria=P)
    L["ceramica_off"] = pbr("Cerâmica off-white", (0.88, 0.85, 0.79), 0.4, coat=0.2, categoria=P)
    L["vidro_globo"] = shadow_transparent(pbr("Vidro soprado fumê", (0.9, 0.9, 0.86), 0.05, transmission=1.0, categoria=P, thin=True))
    L["opalina"] = pbr("Vidro opalino", (0.95, 0.93, 0.88), 0.3, subsurface=0.3, transmission=0.4, categoria=P)
    L["folha"] = pbr("Folhagem", (0.2, 0.33, 0.12), 0.6, tex="leaves_col", tex_m=1.0, alpha_tex=True, subsurface=0.0, categoria="paisagismo")
    L["tronco"] = pbr("Casca de árvore", (0.25, 0.19, 0.14), 0.9, tex="walnut_col", tex_m=0.5, tint=(0.6, 0.55, 0.5), categoria="paisagismo")
    L["vaso"] = pbr("Vaso de cimento", (0.58, 0.55, 0.5), 0.85, tex="concrete_drive_col", tex_m=1.0)
    L["livro_a"] = pbr("Livro A", (0.55, 0.42, 0.3), 0.7, categoria=P)
    L["livro_b"] = pbr("Livro B", (0.82, 0.78, 0.7), 0.7, categoria=P)
    L["livro_c"] = pbr("Livro C", (0.3, 0.36, 0.33), 0.7, categoria=P)
    L["tela_tv"] = pbr("Tela TV", (0.01, 0.01, 0.012), 0.08, 0.0, coat=1.0, categoria=P)
    L["eletro"] = pbr("Eletrodoméstico inox", (0.6, 0.6, 0.58), 0.3, 1.0)
    L["vidro_preto"] = pbr("Vidro preto (cooktop)", (0.01, 0.01, 0.01), 0.05, coat=1.0)
    L["espelho"] = pbr("Espelho", (0.95, 0.95, 0.95), 0.0, 1.0)
    for k, img in (("art_a", "art_a_col"), ("art_b", "art_b_col"), ("art_c", "art_c_col"), ("art_d", "art_d_col")):
        L[k] = pbr("Gravura " + k[-1].upper(), (0.9, 0.86, 0.8), 0.8, tex=img, tex_m=1.0, categoria=P)
    L["led"] = emission("LED 2700K", (1.0, 0.78, 0.52), 6.0)
    L["led_forte"] = emission("LED 2700K forte", (1.0, 0.8, 0.56), 25.0)
    L["lampada"] = emission("Lâmpada quente", (1.0, 0.72, 0.45), 30.0)
    # ---- paleta do vídeo de referência (proposta)
    L["tecido_azul"] = pbr("Tecido azul-petróleo", (0.23, 0.36, 0.47), 0.85, tex="fabric_blue_col", tex_m=0.4, normal="fabric_blue_nrm", nstrength=0.3, sheen=0.4, categoria=P)
    L["tecido_teal"] = pbr("Tecido verde-água", (0.27, 0.47, 0.44), 0.85, tex="fabric_teal_col", tex_m=0.4, normal="fabric_teal_nrm", nstrength=0.3, sheen=0.4, categoria=P)
    L["tecido_cinza"] = pbr("Tecido cinza-claro", (0.69, 0.69, 0.67), 0.9, tex="fabric_gray_col", tex_m=0.4, normal="fabric_gray_nrm", nstrength=0.3, sheen=0.4, categoria=P)
    L["tecido_grafite"] = pbr("Tecido grafite", (0.27, 0.27, 0.28), 0.9, tex="fabric_charcoal_col", tex_m=0.4, normal="fabric_charcoal_nrm", nstrength=0.3, sheen=0.4, categoria=P)
    L["tecido_salmao"] = pbr("Tecido salmão", (0.88, 0.58, 0.5), 0.85, tex="fabric_salmon_col", tex_m=0.4, sheen=0.4, categoria=P)
    L["palha"] = pbr("Palha trançada", (0.77, 0.63, 0.43), 0.75, tex="rattan_col", tex_m=0.25, alpha_tex=True, categoria=P)
    L["muro_verde"] = pbr("Muro verde (trepadeira)", (0.15, 0.3, 0.1), 0.8, tex="hedge_col", tex_m=2.5, normal="hedge_nrm", nstrength=0.8, categoria="paisagismo")
    L["carvalho_claro"] = pbr("Lâmina de carvalho claro", (0.75, 0.63, 0.47), 0.4, tex="oak_pale_col", tex_m=1.0, rough_tex="oak_pale_rgh", categoria=P)
    L["laca_grafite"] = pbr("Laca grafite fosca", (0.12, 0.12, 0.13), 0.45, categoria=P)
    L["azulejo_marinho"] = pbr("Revestimento azul-marinho", (0.13, 0.2, 0.32), 0.18, tex="navy_tile_col", tex_m=1.2, coat=0.4, categoria=P)
    L["nero"] = pbr("Porcelanato marmorizado preto", (0.1, 0.1, 0.1), 0.15, tex="nero_col", tex_m=1.6, rough_tex="nero_rgh", coat=0.3, categoria=P)
    L["concreto_claro"] = pbr("Piso cimentício claro", (0.82, 0.8, 0.77), 0.7, tex="concrete_light_col", tex_m=3.0, rough_tex="concrete_light_rgh", categoria=P)
    L["art_mar1"] = pbr("Quadro mar 1", (0.3, 0.5, 0.7), 0.6, tex="art_mar1_col", tex_m=1.0, categoria=P)
    L["art_mar2"] = pbr("Quadro mar 2", (0.3, 0.5, 0.7), 0.6, tex="art_mar2_col", tex_m=1.0, categoria=P)
    # ---- detalhes das imagens do vídeo de apresentação (proposta)
    L["painel_taupe"] = pbr("Painel de fachada taupe (juntas verticais)", (0.43, 0.39, 0.36), 0.42, tex="plaster_gray_col", tex_m=3.0, tint=(0.36, 0.325, 0.3), coat=0.15, categoria=P)
    L["taupe_escuro"] = pbr("Metal bronze-taupe (testeira, coluna, puxador)", (0.27, 0.24, 0.22), 0.38, 0.6, categoria=P)
    L["junta_escura"] = pbr("Junta de painel", (0.08, 0.075, 0.07), 0.7, categoria=P)
    L["forro_beiral"] = pbr("Forro do beiral — cinza-claro liso", (0.8, 0.79, 0.77), 0.85, categoria=P)
    L["laca_terracota"] = pbr("Laca terracota fosca (marcenaria da cozinha)", (0.55, 0.3, 0.2), 0.55, categoria=P)
    L["grafite_fosco"] = pbr("Cinza grafite fosco (nicho de serviço)", (0.17, 0.17, 0.18), 0.6, categoria=P)
    L["tecido_pied"] = pbr("Tecido pied-de-poule", (0.5, 0.5, 0.5), 0.9, tex="pied_col", tex_m=0.12, sheen=0.3, categoria=P)
    L["tecido_salvia"] = pbr("Tecido sálvia", (0.5, 0.58, 0.48), 0.85, tex="fabric_teal_col", tex_m=0.4, tint=(1.1, 1.05, 0.95), sheen=0.4, categoria=P)
    L["tecido_teal_escuro"] = pbr("Tecido verde-petróleo", (0.15, 0.28, 0.28), 0.8, tex="fabric_teal_col", tex_m=0.4, tint=(0.55, 0.62, 0.65), sheen=0.6, categoria=P)
    L["poster_life"] = pbr("Pôster 'Life'", (0.1, 0.2, 0.15), 0.5, tex="poster_life_col", tex_m=1.0, coat=0.6, categoria=P)
    L["casca_clara"] = pbr("Casca clara (eucalipto)", (0.78, 0.77, 0.73), 0.8, tex="casca_clara_col", tex_m=1.0, categoria="paisagismo")
    L["capim"] = pbr("Capim ornamental", (0.36, 0.55, 0.18), 0.6, subsurface=0.0, categoria="paisagismo")
    L["veneziana"] = pbr("Veneziana de alumínio grafite", (0.16, 0.16, 0.17), 0.45, 0.5, categoria=A)
    from .estilo import ESTILO
    if ESTILO["nome"] == "moderno":
        moderno(L)
    return L

def moderno(L):
    """Paleta contemporânea (PROPOSTA). Troca materiais por chave — todas as peças que usam
    a chave mudam juntas, mantendo continuidade entre ambientes."""
    P = "proposta"
    L["parede_int"] = pbr("Pintura acetinada — branco neve", (0.9, 0.895, 0.88), 0.8, tex="plaster_gray_col", tex_m=2.0, tint=(1.08, 1.08, 1.07), normal="plaster_gray_nrm", nstrength=0.08)
    L["parede_ext"] = pbr("Reboco liso — branco", (0.9, 0.89, 0.87), 0.85, tex="plaster_gray_col", tex_m=2.0, tint=(1.09, 1.09, 1.08), normal="plaster_gray_nrm", nstrength=0.2, categoria="arquitetura")
    L["piso_madeira"] = pbr("Porcelanato 120x120 cinza-claro acetinado", (0.84, 0.83, 0.81), 0.28, tex="porcelain_xl_col", tex_m=2.4, rough_tex="porcelain_xl_rgh", normal="porcelain_xl_nrm", nstrength=0.15, coat=0.15)
    L["tecido_cinza"] = L["boucle"]
    L["tecido_azul"] = L["couro"]
    L["tecido_teal"] = L["veludo_oliva"]
    L["palha"] = pbr("Metal preto fosco (pendentes e vasos)", (0.025, 0.025, 0.027), 0.42, 0.6, categoria=P)
    L["carvalho_claro"] = L["nogueira"]
    L["calacatta"] = pbr("Quartzo branco calacatta", (0.93, 0.92, 0.9), 0.12, tex="calacatta_col", tex_m=1.6, rough_tex="calacatta_rgh", coat=0.3)
    L["latao"] = pbr("Metal preto fosco", (0.02, 0.02, 0.022), 0.45, 0.8)
    L["azulejo_marinho"] = L["pedra_verde"]
    L["tecido_salmao"] = L["ceramica_terracota"]
    L["pedra_fachada"] = pbr("Porcelanato pedra escura 60x120 (fachada)", (0.25, 0.25, 0.25), 0.55, tex="basalto_col", tex_m=2.4, rough_tex="basalto_rgh", normal="basalto_nrm", nstrength=0.5, categoria=P)
    L["forro_madeira"] = pbr("Forro de madeira do beiral (réguas 10 cm)", (0.6, 0.43, 0.28), 0.5, tex="forro_madeira_col", tex_m=1.6, rough_tex="forro_madeira_rgh", normal="forro_madeira_nrm", nstrength=0.3, categoria=P)
