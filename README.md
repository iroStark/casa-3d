# Casa 3D — reconstrução do projeto arquitetônico

Modelo Blender de alta fidelidade, imagens, plantas 3D, vídeo do percurso e site público,
todos gerados **por script** a partir de uma única fonte: o PDF do projeto.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `data/projeto.json` | Base estruturada: eixos, níveis, paredes, vãos, ambientes, terreno e **conflitos**, com status de cada dado (C cotado · G gráfico · X cruzado entre vistas · H hipótese · P proposta) |
| `data/percurso.json` | Percurso da visita (mesmo do vídeo e do site) |
| `scripts/gen_textures.py` | Gera as 69 texturas próprias (numpy, sementes fixas) |
| `scripts/build.py` + `scripts/casa/*` | Gera `blender/casa.blend` do zero (arquitetura, entorno, interiores, luzes, câmeras, percurso) |
| `scripts/validate_plan.py` | Corte do modelo a 1,50 m para sobrepor à folha 02 (`docs/validacao_planta_overlay.png`) |
| `scripts/validate_tour.py` | Ray cast quadro a quadro: a câmera do percurso não atravessa superfícies |
| `scripts/render_stills.py` | Renders Cycles (4K) de todas as câmeras |
| `scripts/render_tour.py` | Vídeo do percurso (EEVEE) + MP4 |
| `scripts/export_web.py` | GLB do site (Draco + WebP) derivado do mesmo `.blend` |
| `scripts/make_ifc.py` | IFC4 (IfcOpenShell) a partir de `data/projeto.json` |
| `web/` | Site (Vite + three.js) |
| `docs/PROCESSO.md` | Decisões, conflitos, versões e validações executadas |

O PDF original e as pranchas rasterizadas ficam em `source/` e **não** são publicados (o carimbo contém nomes e contatos).

## Regenerar tudo

```bash
blender -b -P scripts/gen_textures.py
blender -b --factory-startup -P scripts/build.py -- --stage full --out blender/casa.blend
blender -b blender/casa.blend -P scripts/validate_tour.py
blender -b blender/casa.blend -P scripts/render_stills.py -- --cams all --samples 128 --out renders/4k
blender -b blender/casa.blend -P scripts/render_tour.py -- --res 1920x1080 --samples 48 --encode
blender -b blender/casa.blend -P scripts/export_web.py -- web/public/modelo/casa.glb
.venv/bin/python scripts/make_ifc.py
npm --prefix web ci && npm --prefix web run build && npm --prefix web test
```

Ferramentas: Blender 5.2.2 LTS (Cycles/Metal, EEVEE), IfcOpenShell 0.8.4, ffmpeg, Node 26, Vite 8, three.js 0.186. Semente global `20260612`; Cycles `seed = 612`.
