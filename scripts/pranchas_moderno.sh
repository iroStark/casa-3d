#!/bin/zsh
# Pós-processamento da versão moderna:
#  - pranchas (alçados/cortes, PNG com transparência) sobre fundo branco
#  - JPEGs para o site (web/public/renders/{web,4k}/mod_*.jpg)
#  - PDF de apresentação A3 paisagem (exports/apresentacao_moderna.pdf)
set -e
cd "$(dirname "$0")/.."
SRC=renders/moderno_4k
OUT=renders/moderno_final
mkdir -p $OUT web/public/renders/web web/public/renders/4k exports
F_REG="/System/Library/Fonts/Supplemental/Arial.ttf"
F_BOLD="/System/Library/Fonts/Supplemental/Arial Bold.ttf"

for f in $SRC/*.png; do
  b=$(basename "$f" .png)
  case $b in
    A0*|CT*) magick "$f" -background white -alpha remove -alpha off "$OUT/$b.png" ;;
    *) cp "$f" "$OUT/$b.png" ;;
  esac
  magick "$OUT/$b.png" -quality 90 -sampling-factor 4:2:0 -strip "web/public/renders/4k/mod_$b.jpg"
  magick "$OUT/$b.png" -resize 1600x1600 -quality 82 -strip "web/public/renders/web/mod_$b.jpg"
done

# ---- PDF A3 paisagem (420 x 297 mm a 200 dpi = 3307 x 2339 px)
W=3307; H=2339; M=110
PG=renders/moderno_paginas; rm -rf $PG; mkdir -p $PG
n=0
pagina() {   # titulo  subtitulo  imagens...
  local tit="$1" sub="$2"; shift 2
  local imgs=(); for i in "$@"; do [ -f "$i" ] && imgs+=("$i"); done
  [ ${#imgs[@]} -eq 0 ] && return 0
  [ ${#imgs[@]} -eq 3 ] && imgs=("${imgs[@]:0:2}")
  set -- "${imgs[@]}"
  n=$((n+1)); local p=$(printf "%s/%02d.png" $PG $n)
  local cw=$((W-2*M)); local ch=$((H-2*M-260))
  local k=$#
  if [ $k -eq 1 ]; then
    magick "$1" -resize ${cw}x${ch} /tmp/_casa_bloco.png
  elif [ $k -eq 2 ]; then
    magick "$1" "$2" -resize ${cw}x$(( (ch-40)/2 )) -background white -gravity center -splice 0x0 -append /tmp/_casa_bloco.png
    magick /tmp/_casa_bloco.png -resize ${cw}x${ch} /tmp/_casa_bloco.png
  else
    magick \( "$1" "$2" -resize $(( (cw-40)/2 ))x -background white +append \) \( "$3" "$4" -resize $(( (cw-40)/2 ))x -background white +append \) -append -resize ${cw}x${ch} /tmp/_casa_bloco.png
  fi
  magick -size ${W}x${H} xc:white \
    /tmp/_casa_bloco.png -gravity north -geometry +0+$((M+230)) -composite \
    -gravity northwest -font "$F_BOLD" -pointsize 64 -fill '#2a231d' -annotate +${M}+${M} "$tit" \
    -font "$F_REG" -pointsize 34 -fill '#6b5d4f' -annotate +${M}+$((M+90)) "$sub" \
    -gravity southwest -pointsize 26 -fill '#8a7d70' -annotate +${M}+60 "Casa térrea — versão moderna · mesmas medidas do projeto (PDF). Acabamentos, mobiliário e paisagismo são proposta." \
    -gravity southeast -annotate +${M}+60 "$(printf '%02d' $n)" \
    "$p"
}
O=$OUT
pagina "Casa térrea — versão moderna" "Mesma planta, mesmas medidas; nova linguagem de acabamentos" $O/E04.png
pagina "Implantação e cobertura" "Vista superior do lote 30 × 25 m e perspectivas aéreas" $O/E08.png $O/E06.png $O/E07.png $O/E11.png
pagina "Planta 3D" "Ambientes com nomes; cotas gerais da laje 15,35 × 13,10 m" $O/P04.png
pagina "Planta 3D mobiliada" "Layout baseado na planta mobiliar do projeto" $O/P01.png
pagina "Plantas 3D em perspectiva" "Paredes cortadas a 2,40 m" $O/P02.png $O/P03.png
pagina "Alçados 3D" "Fachada leste (frontal) e fachada norte (lateral direita)" $O/A01.png $O/A02.png
pagina "Alçados 3D" "Fachada sul (lateral esquerda) e fachada oeste (posterior)" $O/A03.png $O/A04.png
pagina "Cortes 3D" "Longitudinal (jantar, cozinha, despensa, garagem) e transversal (suíte 2, corredor, WC, despensa)" $O/CT1.png $O/CT2.png
pagina "Fachadas" "Dia" $O/E01.png $O/E02.png $O/E03.png $O/E05.png
pagina "Fachadas ao entardecer" "Iluminação de beiral, piscina e jardim" $O/E09.png $O/E10.png $O/E12.png $O/E11.png
pagina "Sala, jantar e cozinha" "Ambientes integrados abertos para a piscina" $O/V01.png
pagina "Sala de estar e jantar" "" $O/I01.png $O/I02.png $O/D01.png $O/D02.png
pagina "Cozinha" "" $O/K01.png $O/K02.png $O/K03.png $O/M01.png
pagina "Suíte 1" "" $O/S101.png $O/S102.png $O/S103.png $O/S104.png
pagina "Suíte 2 e corredor" "" $O/S201.png $O/S202.png $O/S203.png $O/C01.png
pagina "Banheiros" "Vistas com a parede cortada (os banheiros não têm janela no projeto)" $O/B01.png $O/B03.png $O/B05.png $O/B06.png
pagina "Apoio" "Despensa, área de serviço e garagem" $O/X01.png $O/X03.png $O/X05.png $O/X06.png
pagina "Detalhes" "" $O/M02.png $O/M03.png $O/I04.png $O/D03.png
magick $PG/*.png -quality 85 -compress jpeg -density 200 exports/apresentacao_moderna.pdf
ls -la exports/apresentacao_moderna.pdf
