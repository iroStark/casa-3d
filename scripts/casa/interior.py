"""Ambientação (PROPOSTA) — posicionada segundo a Planta Mobiliar (pág. 3) e conferida
contra circulação, vãos e raio de abertura das portas. Nada aqui altera a arquitetura.
"""
import math
import bpy
from .core import coll, set_coll, box, cylinder, group, sweep_profile_x, link
from . import furn as F

def G(name, objs, cat="proposta"):
    e = group(name, objs)
    e["categoria"] = cat; e["status"] = "P"
    for o in objs:
        o["categoria"] = cat
    return e

def boiserie(name, M, axis, fixed, a0, a1, z0=0.10, z1=2.90, face=+1, rows=(0.10, 0.95, 1.05, 2.80), cols=None, mat=None):
    """Molduras clássicas aplicadas na parede (quadros de moldura 3 cm)."""
    mat = mat or M["laca_off"]
    objs = []
    t = 0.018; w = 0.03
    cols = cols or max(1, int(round((a1 - a0) / 0.75)))
    gap = 0.10
    pw = (a1 - a0 - gap * (cols + 1)) / cols
    bands = [(rows[0] + 0.08, rows[1]), (rows[2], rows[3])]
    k = 0
    for (zb, zt) in bands:
        for c in range(cols):
            u0 = a0 + gap + c * (pw + gap); u1 = u0 + pw
            for (ua, ub, za, zc) in ((u0, u1, zb, zb + w), (u0, u1, zt - w, zt), (u0, u0 + w, zb, zt), (u1 - w, u1, zb, zt)):
                if axis == "x":   # parede com face perpendicular a X (plano YZ), x fixo
                    xa, xb = (fixed, fixed + t) if face > 0 else (fixed - t, fixed)
                    objs.append(box(f"{name}_m{k}", xa, xb, ua, ub, za, zc, mat)); k += 1
                else:
                    ya, yb = (fixed, fixed + t) if face > 0 else (fixed - t, fixed)
                    objs.append(box(f"{name}_m{k}", ua, ub, ya, yb, za, zc, mat)); k += 1
    # cimalha/chair-rail a 1,00
    if axis == "x":
        xa, xb = (fixed, fixed + 0.025) if face > 0 else (fixed - 0.025, fixed)
        objs.append(box(name + "_cimalha", xa, xb, a0, a1, 0.98, 1.02, mat))
    else:
        ya, yb = (fixed, fixed + 0.025) if face > 0 else (fixed - 0.025, fixed)
        objs.append(box(name + "_cimalha", a0, a1, ya, yb, 0.98, 1.02, mat))
    return G(name, objs)

def build(L):
    M = L
    root = coll("CASA")
    C = coll("09_Mobiliario_e_Decoracao_PROPOSTA", root)
    set_coll(coll("09a_Sala_Jantar_Cozinha", C))
    # ---------------- JANTAR (pág. 3: mesa 8 lugares no sentido N-S)
    TX, TY = 1.40, -3.00
    F.tapete("Tapete_jantar", 2.5, 3.5, M, M["tapete_jantar"], (TX, TY))
    F.mesa_jantar_metal("Mesa_jantar", M, (TX, TY), 0, L=2.40, W=0.95)
    AZ, FE = M["tecido_azul"], M["ferro"]
    for k, y in enumerate((-0.75, 0.0, 0.75)):
        F.cadeira_jantar(f"Cadeira_O{k}", M, (TX - 0.70, TY + y), 90, AZ, FE)
        F.cadeira_jantar(f"Cadeira_L{k}", M, (TX + 0.70, TY + y), -90, AZ, FE)
    F.cadeira_jantar("Cadeira_N", M, (TX, TY + 1.62), 0, AZ, FE)
    F.cadeira_jantar("Cadeira_S", M, (TX, TY - 1.62), 180, AZ, FE)
    # dois pendentes de palha sobre a mesa (vídeo)
    G("Pendentes_palha_jantar", F.pendente_palha("Pendente_palha_N", M, TX, TY + 0.55, 1.62) + F.pendente_palha("Pendente_palha_S", M, TX, TY - 0.55, 1.62), "iluminacao")
    F.planta_vaso("Planta_ficus_jantar", M, (0.45, -4.25, 0), h=1.9, pot_r=0.22, kind="ficus", leaves=220, seed=3)
    # ---------------- COZINHA
    G("Ilha_cozinha", F.ilha("Ilha", M, 3.50, 4.60, -4.65, -1.30))
    for k, y in enumerate((-2.20, -3.00, -3.80)):
        F.banqueta(f"Banqueta{k}", M, (3.02, y), 0, M["tecido_grafite"], M["ferro"])
    G("Coifa_ilha", F.coifa("Coifa", M, 4.15, -1.88))
    G("Marcenaria_nicho", F.torre_nicho("Nicho", M, 5.80, 6.40, -4.65, -1.30))
    F.cristaleira("Cristaleira", M, (5.60, -0.31), 0, w=1.80, d=0.40)
    # ---------------- SALA DE ESTAR (pág. 3: sofá curvo ao norte, TV ao sul, 2 poltronas laterais)
    set_coll(coll("09b_Sala_Estar", C))
    SX, SY = 2.60, -7.92
    F.tapete("Tapete_estar", 3.4, 2.8, M, M["tapete_sala"], (SX, SY - 0.05))
    # sofá cinza em L voltado para a TV (vídeo); chaise a oeste
    F.sofa_L("Sofa_L", M, (2.55, -6.62), 0, L=3.0, chaise=1.75)
    F.mesa_centro("Mesa_centro", M, (2.80, -8.15))
    F.poltrona_concha("Poltrona_concha", M, (4.40, -8.05), -90, M["tecido_azul"])
    F.mesa_lateral("Mesa_lateral_O", M, (0.62, -7.25))
    F.rack_tv("Painel_TV", M, (SX, -9.765), 180, w=3.2, ripado=False)
    G("Painel_madeira_TV", F.painel_madeira("Painel_madeira_TV", M, 0.95, 4.25, -9.80, 0.0, 2.75, face=+1, frisos=0.0))
    F.luminaria_tripe("Luminaria_tripe", M, (0.55, -6.25, 0))
    F.vaso_palha("Vaso_palha_1", M, (0.40, -8.75, 0), h=0.85, r=0.22)
    F.vaso_palha("Vaso_palha_2", M, (0.70, -9.05, 0), h=0.55, r=0.17)
    F.planta_vaso("Planta_palmeira_estar", M, (4.72, -9.40, 0), h=1.7, pot_r=0.2, kind="palmeira", leaves=26, seed=5, pot=M["vaso"])
    F.planta_vaso("Planta_oliveira_estar", M, (0.45, -5.35, 0), h=1.6, pot_r=0.2, kind="oliveira", leaves=420, seed=6, pot=M["ceramica_off"])
    F.quadro("Quadro_estar", M, "art_a", 1.10, 0.85, (5.07, -7.85, 1.75), -90)
    # luminária de piso ao lado do sofá
    lp = [cylinder("Luminaria_piso_base", 0.15, 0.02, (0, 0, 0), 32, M["latao"]),
          cylinder("Luminaria_piso_haste", 0.012, 1.45, (0, 0, 0.02), 12, M["latao"]),
          cylinder("Luminaria_piso_cupula", 0.22, 0.28, (0, 0, 1.40), 40, M["linho_branco"], r2=0.18, cap=False)]
    from .core import sphere
    b = sphere("Luminaria_piso_lampada", 0.035, (0, 0, 1.55), 12, 8, M["lampada"]); b["luz"] = 1
    lp.append(b)
    for o_ in lp:
        bpy.data.objects.remove(o_, do_unlink=True)
    # ---------------- CORREDOR / HALL
    set_coll(coll("09c_Corredor_Hall", C))
    F.tapete("Passadeira_corredor", 6.0, 0.75, M, M["tapete_quarto"], (9.55, -5.35))
    F.aparador("Aparador_hall", M, (11.85, -5.02), 0, w=1.3, d=0.30, h=0.82)
    # o aparador encosta na parede B (face -4.85) com frente para o sul
    F.espelho_banho("Espelho_hall", M, (11.85, -4.87, 1.55), 0, w=0.75, redondo=True)
    F.quadro("Quadro_corredor1", M, "art_c", 0.70, 0.90, (9.15, -5.82, 1.55), 180)
    F.quadro("Quadro_corredor2", M, "art_d", 0.70, 0.90, (12.10, -5.82, 1.55), 180)
    # ---------------- SUITE 2 (pág. 3: duas camas de solteiro) — referência 1 para a atmosfera
    set_coll(coll("09d_Suite2", C))
    G("Armario_suite2", F.guarda_roupa("Armario_S2", M, 5.30, 7.20, -6.65, -6.05, front="-y", mat=M["laca_off"]))
    # parede de madeira atrás das camas (vídeo): réguas verticais de 15 cm com LED no topo
    pr = []
    y = -9.95
    k = 0
    while y < -6.86:
        pr.append(box(f"Regua_S2_{k}", 5.30, 5.33, y + 0.004, min(y + 0.146, -6.85), 0.0, 2.40, M["carvalho_claro"]))
        y += 0.15; k += 1
    pr.append(box("Regua_S2_fundo", 5.296, 5.30, -9.95, -6.85, 0.0, 2.40, M["nogueira"]))
    led = box("LED_paineL_S2", 5.33, 5.34, -9.93, -6.87, 2.41, 2.42, M["led_forte"]); led["luz"] = 1
    pr.append(led)
    G("Painel_madeira_suite2", pr)
    F.tapete("Tapete_suite2", 2.2, 3.0, M, M["tapete_quarto"], (6.75, -8.35))
    for k, y in enumerate((-7.55, -9.15)):
        F.cama(f"Cama_solteiro_{k+1}", M, (5.33 + 1.0, y), 90, W=0.95, L=2.0, cab_h=1.0, cab_mat=M["tecido_cinza"],
               duvet=M["linho_branco"], throw=M["tecido_salmao"], solteiro=True)
    F.criado("Criado_suite2", M, (5.60, -8.35), 90, w=0.42, d=0.38, h=0.52, lamp=False, mat=M["carvalho"])
    G("Pendente_suite2", F.pendente_globo("Pendente_S2", M, 5.62, -8.35, 1.55, 0.13))
    F.espelho_arco("Penteadeira_arco", M, (8.27, -10.10), -90, w=0.75, h=1.25)
    F.cadeira_boucle("Cadeira_penteadeira", M, (7.48, -10.10), 90)
    F.quadro("Quadro_suite2", M, "art_b", 0.45, 0.60, (8.27, -6.95, 1.55), -90)
    F.planta_vaso("Planta_suite2", M, (5.60, -10.70, 0), h=1.0, pot_r=0.14, kind="palmeira", leaves=16, seed=9, pot=M["ceramica_off"])
    # ---------------- SUITE 1 (pág. 3: cama de casal com cabeceira a leste, armário em L)
    set_coll(coll("09e_Suite1", C))
    G("Armario_suite1_norte", F.guarda_roupa("Armario_S1N", M, 11.05, 13.00, -6.65, -6.05, front="-y", mat=M["laca_grafite"]))
    G("Armario_suite1_leste", F.guarda_roupa("Armario_S1L", M, 12.40, 13.00, -7.45, -6.65, front="-x", nportas=2, mat=M["laca_grafite"]))
    G("Cabeceira_estofada_suite1", F.cabeceira_estofada("Cabeceira_S1", M, -11.0, -7.50, 13.00, 0.0, 1.30))
    F.quadro("Quadro_mar_1", M, "art_mar1", 0.75, 0.75, (12.97, -8.72, 1.95), -90, frame=M["laca_grafite"])
    F.quadro("Quadro_mar_2", M, "art_mar2", 0.75, 0.75, (12.97, -9.58, 1.95), -90, frame=M["laca_grafite"])
    # TV na parede oposta à cama (vídeo), sobre rack ripado
    tv = [box("TV_suite1", 10.00, 10.035, -9.55, -8.45, 1.05, 1.68, M["alu_preto"], bevel=0.003),
          box("TV_suite1_tela", 10.035, 10.037, -9.53, -8.47, 1.07, 1.66, M["tela_tv"]),
          box("Rack_suite1", 10.00, 10.40, -9.80, -8.20, 0.30, 0.55, M["carvalho_claro"], bevel=0.004)]
    for k in range(26):
        y = -9.80 + k * 0.0615
        tv.append(box(f"Rack_suite1_ripa{k}", 10.40, 10.42, y, y + 0.045, 0.31, 0.54, M["carvalho_claro"]))
    G("TV_suite1", tv)
    F.tapete("Tapete_suite1", 2.6, 3.2, M, M["tapete_quarto"], (11.55, -9.15), 90)
    F.cama("Cama_casal", M, (12.89 - 1.025, -9.15), -90, W=1.80, L=2.05, cab_h=0.45, cab_mat=M["tecido_grafite"],
           duvet=M["tecido_cinza"], throw=M["tecido_grafite"])
    F.criado("Criado_S1_N", M, (12.66, -7.78), -90, mat=M["laca_grafite"])
    F.criado("Criado_S1_S", M, (12.66, -10.52), -90, mat=M["laca_grafite"])
    F.poltrona_concha("Poltrona_suite1", M, (10.55, -10.50), 145, M["tecido_teal"])
    # ---------------- BANHEIROS (pág. 3: box ao norte em ambos; bacia/lavatório conforme planta)
    set_coll(coll("09f_Banheiros", C))
    G("Box_WC_suite2", F.box_chuveiro("Box_S2", M, 8.50, 9.80, -7.05, -6.05))
    F.bacia("Bacia_WC_suite2", M, (8.50 + 0.28, -7.42), 90)
    F.bancada_banho("Bancada_WC_suite2", M, (9.80 - 0.24, -7.98), -90, w=0.80, d=0.48)
    F.espelho_banho("Espelho_WC_suite2", M, (9.775, -7.98, 1.50), -90, w=0.70, h=0.85)
    F.toalheiro("Toalheiro_WC_suite2", M, (9.15, -8.50), 180, w=0.5)
    G("Box_WC_suite1", F.box_chuveiro("Box_S1", M, 8.50, 9.80, -9.65, -8.65))
    F.bacia("Bacia_WC_suite1", M, (9.80 - 0.28, -10.02), -90)
    F.bancada_banho("Bancada_WC_suite1", M, (8.50 + 0.24, -10.68), 90, w=0.90, d=0.48, cubas=1)
    F.espelho_banho("Espelho_WC_suite1", M, (8.525, -10.68, 1.50), 90, w=0.75, h=0.90)
    # lavabo/WC social: bancada dupla na parede norte (pág. 3), bacia no canto sudeste
    F.bancada_banho("Bancada_WC_social", M, (7.22, -2.95 - 0.24), 0, w=1.10, d=0.48, cubas=2, mat=M["nogueira"], top=M["pedra_verde"])
    F.espelho_banho("Espelho_WC_social", M, (7.22, -2.975, 1.55), 0, w=0.95, h=0.80)
    F.bacia("Bacia_WC_social", M, (8.30 - 0.28, -4.20), -90)
    # ---------------- DESPENSA
    set_coll(coll("09g_Despensa_Servico_Garagem", C))
    prat = []
    for k, z in enumerate((0.45, 0.85, 1.25, 1.65, 2.05)):
        prat.append(box(f"Despensa_prat_O{k}", 6.55, 6.95, -2.78, -1.32, z, z + 0.025, M["carvalho"]))
        prat.append(box(f"Despensa_prat_S{k}", 6.95, 8.28, -2.78, -2.43, z, z + 0.025, M["carvalho"]))
        for j in range(4):
            prat.append(cylinder(f"Despensa_pote{k}{j}", 0.06, 0.18, (6.75, -1.55 - j * 0.32, z + 0.025), 16,
                                 [M["vidro_globo"], M["ceramica_off"], M["palha"], M["ceramica_terracota"]][(j + k) % 4]))
    G("Despensa_prateleiras", prat)
    # ---------------- ÁREA DE SERVIÇO (nicho externo 1,20 / 0,60 / 1,20)
    sv = [box("Maquina_lavar", 0.95, 1.55, -10.50, -10.02, 0.0, 0.85, M["laca_branca"], bevel=0.02),
          cylinder("Maquina_porta", 0.17, 0.02, (1.25, -10.50, 0.48), 40, M["vidro_preto"], axis="Y"),
          box("Tanque_gabinete", 1.58, 2.08, -10.50, -10.02, 0.0, 0.86, M["laca_off"]),
          box("Tanque_tampo", 1.58, 2.08, -10.50, -10.02, 0.86, 0.90, M["calacatta"]),
          box("Servico_prat1", 0.92, 2.08, -10.40, -10.02, 1.55, 1.58, M["carvalho"]),
          box("Servico_prat2", 2.27, 2.88, -10.42, -10.02, 0.9, 0.93, M["carvalho"]),
          box("Servico_prat3", 2.27, 2.88, -10.42, -10.02, 1.5, 1.53, M["carvalho"]),
          cylinder("Aquecedor", 0.22, 1.10, (3.70, -10.25, 0.9), 40, M["laca_branca"])]
    sv[1].rotation_euler = (math.pi / 2, 0, 0); sv[1].location = (1.25, -10.50, 0.48)
    G("Servico_equipamentos", sv)
    # ---------------- GARAGEM — armários na parede sul (face -4.65)
    G("Armario_garagem", F.guarda_roupa("Armario_garagem", M, 9.20, 12.60, -4.65, -4.25, h=2.10, front="+y", mat=M["laca_off"]))
    F.planta_vaso("Planta_garagem", M, (12.55, -0.55, 0), h=1.5, pot_r=0.25, kind="palmeira", leaves=24, seed=13, pot=M["vaso"])
    # ---------------- CORTINAS (linho), sob a sanca
    set_coll(coll("09h_Cortinas", C))
    cur = []
    cur.append(F.cortina("Cortina_JV01_O", M, M["voil"], 0.70, 1.45, 0.0, True, -1))
    cur.append(F.cortina("Cortina_JV01_L", M, M["voil"], 3.85, 4.55, 0.0, True, -1))
    cur.append(F.cortina("Cortina_JV03_S", M, M["voil"], -4.60, -3.90, 0.0, False, +1))
    cur.append(F.cortina("Cortina_JV04_N", M, M["voil"], -5.80, -5.10, 0.0, False, +1))
    cur.append(F.cortina("Cortina_JV04_S", M, M["voil"], -8.95, -8.05, 0.0, False, +1))
    cur.append(F.cortina("Cortina_JV07_O", M, M["blackout"], 5.35, 6.05, -11.15, True, +1))
    cur.append(F.cortina("Cortina_JV07_L", M, M["voil"], 7.45, 8.25, -11.15, True, +1))
    cur.append(F.cortina("Cortina_JV08_O", M, M["voil"], 10.05, 10.75, -11.15, True, +1))
    cur.append(F.cortina("Cortina_JV08_L", M, M["blackout"], 12.15, 12.95, -11.15, True, +1))
    G("Cortinas", cur)
