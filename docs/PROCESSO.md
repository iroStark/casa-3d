# Processo, decisões e validações

## 1. Fonte e revisão
- Fonte única da arquitetura: o PDF de 28 páginas (raster, sem texto extraível). Lido página a página em resolução nativa (1787 × 1263 px por prancha).
- Revisão principal: folhas CAD de ARQUITECTURA datadas de 12/06/2026 (folhas 01 fundação, 02 cotas, 03 cortes, 04 mobiliar, 05 cobertura, 08 alçados, elétrica, esgoto) e pormenores estruturais.
- A folha 02 foi editada (lote 30 × 25 m e piscina 2,50 × 9,50 m) em escala gráfica diferente da casa — medidas da piscina e do lote foram lidas das cotas, a posição foi inferida.
- Páginas 26–28: imagens de apresentação com marca d'água e nota "medidas aproximadas"; alturas incoerentes com os cortes (ex.: "15,00 m"). Usadas só como referência visual secundária, nunca como cota.
- Referências de interiores: as duas imagens anexadas. Links do Instagram: o post 1 abriu (maquete física sobre base acrílica com o modelo na tela); o post 3 abriu parcialmente (vídeo de planta convertida por IA; apenas quadro inicial e comentários visíveis); o reel 2 retornou "Post não está disponível".

## 2. Ancoragem e coordenadas
- Origem (0,0,0) no cruzamento dos eixos 1 e A, no piso acabado. +X leste, +Y norte, metros.
- Eixos da fundação (cotados): X 0 / 5,20 / 8,40 / 9,90 / 13,10 ; Y 0 / −4,75 / −4,85 / −5,95 / −9,90 / −11,15.
- A planta de cotas foi medida em pixel e mapeada nos eixos (100 px/m horizontal no recorte 3×, ~103 px/m vertical). Paredes externas centradas nos eixos (0,20 m).
- Validação: corte do modelo a 1,50 m sobreposto à folha 02 (`docs/validacao_planta_overlay.png`) — paredes e vãos coincidem visualmente em todos os ambientes.

## 3. Alturas (cortes A/A e B/B)
Piso 0,00 · portas 2,10 · vidros e fundo de viga 2,90 · forro 3,05 · laje 3,20–3,40 · vigas 20 × 30.

## 4. Conflitos registrados (não forçados)
Ver `data/projeto.json → conflitos`. Principais: cadeias de cotas norte e oeste que não fecham com os eixos (adotada a geometria dos eixos e das fachadas, panos de ≈3,95 m); cota D–F 5,00 vs. 5,20 medidos em três pranchas (adotado F = −11,15); numeração de eixos diferente no topo e na base da fundação; rótulos dos cortes trocados em relação às linhas de corte; banheiros sem ventilação indicada.

## 5. Camadas do modelo
| Coleção | Conteúdo | Status |
|---|---|---|
| 02 Paredes e Pilares, 03 Estrutura, 04 Esquadrias, 05 Pisos e Forros, 06 Laje | Arquitetura documentada | C/G/X (propriedades `status` e `fonte` em cada objeto) |
| 01 Terreno, 01b Piscina, 01c Muro | Implantação | Lote/piscina C; muro, profundidade e caimentos H |
| 09 Mobiliário e Decoração | Ambientação | P (sobre a planta mobiliar da folha 04) |
| 11 Paisagismo | Vasos nas fachadas (X) e árvores/maciços (P) | X/P |
| 12 Iluminação | Pontos da planta elétrica (posições aproximadas), LEDs de sanca, beiral | G/P |
| 13 Sol e Céu, 14 Câmeras | Luz natural, 48 câmeras fixas + CAM_PERCURSO | — |
| 00 Referências PDF | Folha 02 como plano de conferência (oculto no render) | — |

## 6. Técnico × visualização
- **IFC4** (`exports/casa.ifc`, IfcOpenShell 0.8.4): paredes com aberturas subtraídas, portas, janelas, lajes, pilares, vigas, espaços e piscina, com `Pset_Reconstrucao` (fonte/status). Validado: 0 erros de schema; 104 geometrias geradas sem falha. Não é um BIM executivo: não há famílias, camadas construtivas nem quantitativos.
- **Revit (.rvt)**: não produzido — o Revit não está disponível neste ambiente (macOS sem Autodesk). O IFC pode ser vinculado/importado no Revit.
- **Blender**: modelo de visualização com a mesma base geométrica + ambientação proposta.
