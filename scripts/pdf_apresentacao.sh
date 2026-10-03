#!/bin/zsh
# PDF profissional de apresentação (A3 paisagem, 200 dpi) a partir de uma pasta de renders.
# uso: zsh scripts/pdf_apresentacao.sh renders/v2_4k exports/apresentacao_casa.pdf
set -e
cd "$(dirname "$0")/.."
SRC=${1:-renders/v2_4k}
PDF=${2:-exports/apresentacao_casa.pdf}
OUT=$SRC/_prontas; mkdir -p $OUT
PG=$SRC/_paginas; rm -rf $PG; mkdir -p $PG
F_REG="/System/Library/Fonts/Supplemental/Arial.ttf"
F_BOLD="/System/Library/Fonts/Supplemental/Arial Bold.ttf"
TINTA='#24201c'; CINZA='#6f655b'; LINHA='#cfc6bb'
W=3307; H=2339; M=100; RODAPE=170
DATA="outubro de 2026"

# pranchas técnicas (PNG transparente) -> fundo branco
for f in $SRC/*.png(N); do
  b=$(basename "$f" .png)
  case $b in A0*|CT*) magick "$f" -background white -alpha remove -alpha off "$OUT/$b.png" ;; *) [ -f "$OUT/$b.png" ] || cp "$f" "$OUT/$b.png" ;; esac
done
O=$OUT
TOTAL=23
n=0

carimbo() {  # $1 imagem de página, $2 título da prancha
  magick "$1" \
    -fill none -stroke "$LINHA" -strokewidth 3 -draw "line $M,$((H-RODAPE)) $((W-M)),$((H-RODAPE))" -stroke none \
    -font "$F_BOLD" -pointsize 30 -fill "$TINTA" -gravity northwest -annotate +$M+$((H-RODAPE+30)) "RESIDÊNCIA TÉRREA — APRESENTAÇÃO 3D" \
    -font "$F_REG" -pointsize 24 -fill "$CINZA" -annotate +$M+$((H-RODAPE+76)) "Medidas conforme o projeto arquitetônico (PDF). Revestimentos, mobiliário e paisagismo: proposta de ambientação." \
    -font "$F_REG" -pointsize 26 -fill "$TINTA" -gravity northeast -annotate +$((M+330))+$((H-RODAPE+30)) "$2" \
    -font "$F_REG" -pointsize 24 -fill "$CINZA" -annotate +$((M+330))+$((H-RODAPE+76)) "$DATA" \
    -font "$F_BOLD" -pointsize 54 -fill "$TINTA" -annotate +$M+$((H-RODAPE+38)) "$(printf '%02d/%02d' $n $TOTAL)" \
    "$1"
}

pagina() {   # título  subtítulo  imagens...
  local tit="$1" sub="$2"; shift 2
  local imgs=(); for i in "$@"; do [ -f "$i" ] && imgs+=("$i"); done
  [ ${#imgs[@]} -eq 0 ] && return 0
  [ ${#imgs[@]} -eq 3 ] && imgs=("${imgs[@]:0:2}")
  set -- "${imgs[@]}"
  n=$((n+1)); local p=$(printf "%s/%02d.png" $PG $n)
  local top=$((M+190)); local cw=$((W-2*M)); local ch=$((H-top-RODAPE-50))
  if [ $# -eq 1 ]; then
    magick "$1" -resize ${cw}x${ch} /tmp/_bl.png
  elif [ $# -eq 2 ]; then
    local w1=$(magick identify -format %w "$1") h1=$(magick identify -format %h "$1")
    if [ $(( w1 * 10 / h1 )) -ge 20 ]; then   # imagens largas (alçados/cortes): uma sobre a outra
      magick "$1" "$2" -resize ${cw}x$(( (ch-30)/2 )) -background white -gravity center -extent ${cw}x$(( (ch-30)/2 )) -append /tmp/_bl.png
    else
      magick "$1" "$2" -resize $(( (cw-40)/2 ))x${ch} -background white -gravity center -extent $(( (cw-40)/2 ))x${ch} +append /tmp/_bl.png
    fi
  else
    local cw2=$(( (cw-40)/2 )) ch2=$(( (ch-40)/2 )) k=0
    for im in "$1" "$2" "$3" "$4"; do
      k=$((k+1)); magick "$im" -resize "${cw2}x${ch2}^" -gravity center -extent ${cw2}x${ch2} +repage /tmp/_t$k.png
    done
    magick \( /tmp/_t1.png /tmp/_t2.png -background white -bordercolor white -border 20x20 +append \) \
           \( /tmp/_t3.png /tmp/_t4.png -background white -bordercolor white -border 20x20 +append \) -append -shave 20x20 /tmp/_bl.png
  fi
  magick -size ${W}x${H} xc:white /tmp/_bl.png -gravity north -geometry +0+$top -composite \
    -gravity northwest -font "$F_BOLD" -pointsize 62 -fill "$TINTA" -annotate +$M+$M "$tit" \
    -font "$F_REG" -pointsize 32 -fill "$CINZA" -annotate +$M+$((M+88)) "$sub" "$p"
  carimbo "$p" "$tit"
}

texto() {   # título  corpo(arquivo de texto)  [imagem lateral]
  n=$((n+1)); local p=$(printf "%s/%02d.png" $PG $n)
  magick -size ${W}x${H} xc:white \
    -gravity northwest -font "$F_BOLD" -pointsize 62 -fill "$TINTA" -annotate +$M+$M "$1" \
    \( -size 1650x -background white -fill "$TINTA" -font "$F_REG" -pointsize 38 -interline-spacing 14 caption:@"$2" \) -geometry +$M+$((M+170)) -composite "$p"
  if [ -n "$3" ] && [ -f "$3" ]; then
    magick "$p" \( "$3" -resize 1450x1650 \) -gravity northeast -geometry +$M+$((M+170)) -composite "$p"
  fi
  carimbo "$p" "$1"
}

# ---------------- 01 capa
n=1; p=$(printf "%s/%02d.png" $PG $n)
CAPA=$O/V05.png; [ -f $CAPA ] || CAPA=$O/E04.png
magick $CAPA -resize ${W}x${H}^ -gravity center -extent ${W}x${H} \
  \( -size ${W}x760 gradient:'rgba(20,17,14,0)'-'rgba(20,17,14,0.82)' \) -gravity south -composite \
  -gravity southwest -font "$F_BOLD" -pointsize 120 -fill white -annotate +150+330 "Residência térrea" \
  -font "$F_REG" -pointsize 54 -fill '#efe7dc' -annotate +155+240 "Apresentação 3D — plantas, alçados, cortes e ambientes" \
  -font "$F_REG" -pointsize 34 -fill '#d9cfc2' -annotate +155+160 "Reconstruída a partir do projeto arquitetônico · $DATA" "$p"

# ---------------- 02 ficha técnica + paleta
cat > /tmp/_ficha.txt <<'TXT'
DADOS DO PROJETO (conforme o PDF)
•  Lote: 30,00 × 25,00 m (folha 02)
•  Laje de cobertura: 15,35 × 13,10 m, plana, com caimento leve para as quatro bordas
•  Piso acabado ±0,00 · portas 2,10 m · vidros 2,90 m · forro 3,05 m · laje 3,20–3,40 m
•  Paredes de 0,20 m, eixos estruturais da folha de fundação
•  Piscina 2,50 × 9,50 m

AMBIENTES
Sala de estar (5,00 m de largura) · sala de jantar e cozinha integradas com ilha (1,10 × 3,35 m) · despensa · WC social · corredor (1,00 m) · suíte 1 e suíte 2 (3,00 m de largura cada) com banheiros (1,30 m) · garagem coberta aberta · área de serviço · piscina com deck

LINGUAGEM PROPOSTA
Fachada de entrada em painéis taupe com juntas verticais e porta pivotante lisa; testeira fina bronze; plataforma de concreto claro "flutuando" sobre o gramado; placas-degrau com balizadores; caixilhos pretos; interiores em tons claros com piso amadeirado, marcenaria terracota na cozinha, ilha em pedra, sofá cinza, cadeiras azuis, pendentes de palha e trilhos pretos com spots.

Hipóteses (não constam do PDF) estão marcadas no modelo e listadas na última prancha.
TXT
for t in painel_taupe oak_light pedra_cinza laca_terracota fabric_blue deck_gray pool_tiles_aqua hedge; do
  :
done
magick -size 1400x1500 xc:white \
  \( textures/plaster_gray_col.png -resize 300x300^ -extent 300x300 -fill '#6f655c' -colorize 72% \) -geometry +0+0 -composite \
  \( textures/oak_light_col.png -resize 300x300^ -extent 300x300 \) -geometry +350+0 -composite \
  \( textures/pedra_cinza_col.png -resize 300x300^ -extent 300x300 \) -geometry +700+0 -composite \
  \( -size 300x300 xc:'#8c4e34' \) -geometry +1050+0 -composite \
  \( textures/fabric_blue_col.png -resize 300x300^ -extent 300x300 \) -geometry +0+420 -composite \
  \( textures/deck_gray_col.png -resize 300x300^ -extent 300x300 -modulate 115 \) -geometry +350+420 -composite \
  \( textures/pool_tiles_aqua_col.png -resize 300x300^ -extent 300x300 \) -geometry +700+420 -composite \
  \( textures/hedge_col.png -resize 300x300^ -extent 300x300 \) -geometry +1050+420 -composite \
  -font "$F_REG" -pointsize 24 -fill "$TINTA" \
  -annotate +0+330 "Painel taupe (fachada)" -annotate +350+330 "Piso amadeirado" -annotate +700+330 "Pedra cinza (ilha)" -annotate +1050+330 "Laca terracota" \
  -annotate +0+750 "Tecido azul (cadeiras)" -annotate +350+750 "Deck claro" -annotate +700+750 "Pastilha da piscina" -annotate +1050+750 "Muro verde" \
  /tmp/_paleta.png
texto "Ficha técnica e paleta" /tmp/_ficha.txt /tmp/_paleta.png

pagina "Implantação — planta humanizada cotada" "Lote 30 × 25 m, casa, piscina e acessos. Cotas: medidas documentadas no projeto" $O/P05.png
pagina "Planta 3D" "Ambientes com nomes; cotas gerais da laje" $O/P04.png
pagina "Planta 3D mobiliada" "Layout sobre a planta mobiliar do projeto" $O/P01.png
pagina "Plantas 3D em perspectiva" "Paredes cortadas a 2,40 m" $O/P02.png $O/P03.png
pagina "Alçados 3D" "Fachada leste (frontal) e fachada norte (lateral direita) — níveis dos cortes do projeto" $O/A01.png $O/A02.png
pagina "Alçados 3D" "Fachada sul (lateral esquerda) e fachada oeste (posterior)" $O/A03.png $O/A04.png
pagina "Cortes 3D" "Longitudinal: jantar, cozinha, despensa e garagem · transversal: suíte 2, corredor, WC e despensa" $O/CT1.png $O/CT2.png
pagina "Cobertura e vistas aéreas" "Laje plana com beiral de cerca de 1 m em todos os lados" $O/E08.png $O/E06.png $O/E07.png $O/E11.png
pagina "Fachada de entrada" "Painéis taupe, porta pivotante, plataforma flutuante e placas-degrau" $O/V05.png
pagina "Entrada e garagem" "Garagem coberta aberta para norte e leste" $O/V06.png $O/E01.png $O/E02.png $O/E09.png
pagina "Salas abertas para a piscina" "Panos de vidro de piso a 2,90 m na fachada oeste" $O/V02.png
pagina "Piscina e terraço" "Piscina 2,50 × 9,50 m com deck" $O/V03.png $O/E04.png $O/E10.png $O/M02.png
pagina "Fachada sul e área de serviço" "Nicho de serviço com venezianas grafite" $O/V04.png $O/E05.png $O/X03.png $O/E12.png
pagina "Sala de estar" "Sofá modular, mesa orgânica em nogueira e vista para a piscina" $O/V07.png
pagina "Sala de estar e jantar" "" $O/V01.png $O/I01.png $O/D01.png $O/D02.png
pagina "Cozinha" "Marcenaria terracota, ilha em pedra e trilho com pendentes" $O/K01.png $O/K02.png $O/K03.png $O/M01.png
pagina "Corredor e suíte 1" "" $O/C01.png $O/S101.png $O/S102.png $O/S103.png
pagina "Suíte 2" "" $O/S201.png $O/S202.png $O/S203.png $O/S104.png
pagina "Banheiros" "Vistas com a parede cortada (os banheiros não têm janela no projeto)" $O/B01.png $O/B03.png $O/B05.png $O/B06.png
pagina "Apoio" "Despensa, garagem e detalhes" $O/X01.png $O/X02.png $O/X05.png $O/X06.png

cat > /tmp/_notas.txt <<'TXT'
O QUE É DO PROJETO
Eixos, paredes, vãos, portas e sentido de abertura, alturas dos cortes, laje, piscina e lote seguem o PDF. As cotas mostradas nas pranchas são valores escritos no projeto.

HIPÓTESES ADOTADAS (não constam do PDF)
•  Larguras dos panos de vidro da sala (≈ 3,95 m), medidas no desenho: as cotas escritas não fecham com os eixos.
•  Eixo da fachada sul das suítes pelo desenho (cota escrita 5,00 m; desenho ≈ 5,20 m).
•  Profundidade da piscina (1,40 m), muro (2,00 m), caimento da laje (1%), nível do gramado e norte.
•  Altura da porta de entrada (2,90 m) lida na fachada.

PROPOSTA DE AMBIENTAÇÃO
Revestimentos de fachada (2 cm sobre a face, sem alterar vãos), mobiliário, iluminação decorativa, paisagismo, placas-degrau, portão de pedestres e acesso de veículos.

PARA VALIDAR COM O ENGENHEIRO
•  Ventilação dos três banheiros (sem janela no projeto).
•  Cadeias de cotas que não somam a distância entre eixos e a cota de 5,00 m entre os eixos D–F.
•  Rótulos dos cortes A/A e B/B trocados em relação às linhas de corte.
TXT
texto "Notas de fidelidade" /tmp/_notas.txt

ls $PG | wc -l
magick $PG/*.png -quality 86 -compress jpeg -density 200 -units PixelsPerInch "$PDF"
ls -la "$PDF"
