#!/bin/zsh
# Converte os renders 4K (PNG) em JPEG para o site e monta os pacotes da release.
set -e
cd "$(dirname "$0")/.."
mkdir -p web/public/renders/4k web/public/renders/web web/public/video exports
for f in renders/4k/*.png; do
  b=$(basename "$f" .png)
  magick "$f" -quality 90 -sampling-factor 4:2:0 -strip "web/public/renders/4k/$b.jpg"
  magick "$f" -resize 1600x1600 -quality 82 -sampling-factor 4:2:0 -strip "web/public/renders/web/$b.jpg"
done
[ -f video/visita.mp4 ] && cp video/visita.mp4 web/public/video/visita.mp4
cp data/percurso.json data/projeto.json web/public/dados/
rm -f exports/renders_4k.zip exports/casa_blender.zip
(cd web/public/renders && zip -q -r ../../../exports/renders_4k.zip 4k)
(cd exports && zip -q casa_blender.zip casa_empacotado.blend LEIA-ME_blender.txt)
ls -la exports
