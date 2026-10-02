#!/bin/zsh
# Render completo: 50 imagens 4K + quadros do vídeo + MP4 (mesmo blender/casa.blend).
cd "$(dirname "$0")/.."
rm -f video/frames/*.png(N)
blender -b blender/casa.blend -P scripts/render_stills.py -- --cams all --samples 48 --out renders/4k > renders/4k_log.txt 2>&1
blender -b blender/casa.blend -P scripts/render_stills.py -- --cams B01,B02,B03,B04,B05,B06,X01,X02 --samples 64 --out renders/4k > renders/4k_banhos_log.txt 2>&1
blender -b blender/casa.blend -P scripts/render_tour.py -- --res 1280x720 --samples 16 --step 2 > video/tour_log.txt 2>&1
ffmpeg -y -framerate 12 -pattern_type glob -i 'video/frames/*.png' \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -movflags +faststart video/visita.mp4 > video/ffmpeg_log.txt 2>&1
echo RENDER_TUDO_OK
