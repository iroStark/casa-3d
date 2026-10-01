#!/bin/zsh
# Re-render dos ambientes sem janela + quadros do vídeo (12 q/s reais) + MP4 interpolado a 24 q/s.
cd "$(dirname "$0")/.."
blender -b blender/casa.blend -P scripts/render_stills.py -- --cams B01,B02,B03,B04,B05,B06,X01,X02,X05,M01 --samples 64 --out renders/4k > renders/4k_banhos_log.txt 2>&1
blender -b blender/casa.blend -P scripts/render_tour.py -- --res 1280x720 --samples 16 --step 2 > video/tour_log.txt 2>&1
ffmpeg -y -framerate 12 -pattern_type glob -i 'video/frames/*.png' \
  -vf "minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -movflags +faststart video/visita.mp4 > video/ffmpeg_log.txt 2>&1
echo CADEIA_OK
