#!/bin/zsh
# Versão 2 (estilo das imagens do vídeo): banheiros em 4K + vídeo do percurso + MP4.
cd "$(dirname "$0")/.."
blender -b blender/casa.blend -P scripts/render_stills.py -- --cams B01,B02,B03,B04,B05,B06 --samples 64 --out renders/v2_4k > renders/v2_banhos_log.txt 2>&1
rm -f video/frames/*.png(N)
blender -b blender/casa.blend -P scripts/render_tour.py -- --res 1280x720 --samples 16 --step 2 > video/tour_log.txt 2>&1
ffmpeg -y -framerate 12 -pattern_type glob -i 'video/frames/*.png' \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -movflags +faststart video/visita.mp4 > video/ffmpeg_log.txt 2>&1
echo CADEIA_V2_OK
