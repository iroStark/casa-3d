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
| 13 Sol e Céu, 14 Câmeras | Luz natural, 49 câmeras fixas + CAM_PERCURSO | — |
| 00 Referências PDF | Folha 02 como plano de conferência (oculto no render) | — |

## 6. Técnico × visualização
- **IFC4** (`exports/casa.ifc`, IfcOpenShell 0.8.4): paredes com aberturas subtraídas, portas, janelas, lajes, pilares, vigas, espaços e piscina, com `Pset_Reconstrucao` (fonte/status). Validado: 0 erros de schema; 104 geometrias geradas sem falha. Não é um BIM executivo: não há famílias, camadas construtivas nem quantitativos.
- **Revit (.rvt)**: não produzido — o Revit não está disponível neste ambiente (macOS sem Autodesk). O IFC pode ser vinculado/importado no Revit.
- **Blender**: modelo de visualização com a mesma base geométrica + ambientação proposta.

## 7. Imagens, vídeo e site
- 49 câmeras fixas, todas renderizadas do mesmo `blender/casa.blend` em 3840 × 2160 (plantas e cobertura em 3200–3840 px quadrados), Cycles/Metal, 48–64 amostras + OIDN. Interiores com câmera nivelada e deslocamento de lente (verticais retas), lentes 20–40 mm.
- Banheiros e despensa não têm janela no projeto: são mostrados como **vistas com a parede cortada** (plano de corte da câmera atravessando a parede vizinha), identificadas assim nas legendas.
- Vídeo: `CAM_PERCURSO` renderizada no Cycles a 1280 × 720, 12 quadros reais por segundo, interpolados para 24 q/s no ffmpeg (minterpolate). O EEVEE foi testado e descartado (interiores escuros e azulados; 29 s/quadro).
- Site: Vite + three.js; GLB de 4,7 MB (Draco + WebP) exportado do mesmo `.blend`; percurso da rolagem = `data/percurso.json` (o mesmo do vídeo).

## 8. Validações executadas
- Sobreposição do corte do modelo a 1,50 m sobre a folha 02 (`docs/validacao_planta_overlay.png`).
- `scripts/validate_tour.py`: ray cast quadro a quadro (1.741 quadros) — 0 travessias e folga ≥ 0,18 m (folhas de plantas excluídas da folga). Rodado após cada rebuild.
- IFC: 0 erros de schema (ifcopenshell.validate), 104/104 geometrias geradas.
- `.blend` empacotado aberto isoladamente em outra pasta: 59 imagens, todas embutidas; 50 câmeras; percurso 1–1741 com animação.
- Varredura do `.blend`, do GLB, do IFC, do bundle JS, do HTML e do `projeto.json` publicados contra a lista local de termos do carimbo: nada encontrado. A prancha usada como referência no `.blend` teve o carimbo apagado.
- Site em produção (`npm run build` + `npm test`): todos os arquivos referenciados existem no `dist`.
- Navegador: carregamento do GLB, capítulos, menu móvel (Esc e foco), modo de exploração (entrada, cobertura, Esc/retorno), lightbox (setas, fechar, retorno de foco), filtros e downloads — no endereço público, sem autenticação.

## 9. Revisão de estilo a partir do vídeo de apresentação (02/10/2026)
- Referência: vídeo "Casa Térrea - Moderna, Prática e Confortável" (YouTube), com a mesma marca d'água das imagens das págs. 26–28 do PDF. A vista aérea em corte do vídeo mostra a mesma distribuição (garagem com carro, duas suítes com banheiros entre elas, suíte com duas camas de solteiro, nicho de serviço, piscina na lateral).
- Só foi possível ver 4 quadros públicos do vídeo (miniatura e quadros automáticos do YouTube).
- Mudou apenas a **ambientação** (proposta): piso porcelanato amadeirado claro, paredes cinza-claro, caixilhos pretos, forro liso com perfil linear de LED preto, cadeiras azul-petróleo, mesa clara com base preta, dois pendentes de palha, sofá cinza em L, painel liso de madeira na TV, ilha em pedra cinza, suíte 1 com armário grafite, cabeceira estofada grafite com LED e quadros de mar, suíte 2 com parede de réguas de madeira e almofadas salmão, WC social azul-marinho, banheiro da suíte 1 em marmorizado preto, muro coberto de trepadeira, dracenas, poltronas verde-água no terraço, deck claro e piscina turquesa, piso ligando o terraço à piscina (como na pág. 26).
- A arquitetura (paredes, vãos, alturas, laje, posição da piscina) continua a do PDF. Nova câmera V01 reproduz o enquadramento de abertura do vídeo.
- Correção encontrada nesta revisão: o plano de gramado do entorno passava acima do fundo da piscina; foi recortado fora do lote.

## 10. Versão 2 — linguagem das imagens do vídeo de apresentação (03/10/2026)
- Referência: 10 quadros do vídeo enviados pelo proprietário (fachada de entrada, garagem, piscina, nicho de serviço, corredor, sala e a planta humanizada cotada). A planta do vídeo tem as mesmas medidas do projeto (15,35; 3,00; 1,30; 1,00; 5,00; piscina 2,50 × 9,50).
- Fachada leste em painéis taupe com juntas verticais (2 cm sobre a face), porta pivotante lisa com puxador preto e fechadura digital, testeira bronze, forro do beiral claro, coluna escura na garagem, venezianas grafite no nicho de serviço.
- Entorno: plataforma de concreto 17 cm acima do gramado (hipótese de nível), placas-degrau flutuantes com balizadores, touceiras de capim, árvore de tronco claro, portão de pedestres em frente à entrada.
- Interiores: sofá modular cinza com almofadas pied-de-poule/couro/sálvia, mesa de centro orgânica em nogueira, poltrona verde-petróleo, pôster "Life", marcenaria terracota com geladeira inox, ilha em pedra, trilhos pretos com spots e pendentes, batentes de madeira.
- Novas câmeras V02–V07 reproduzem os enquadramentos das imagens; P05 é a planta humanizada cotada; pranchas A01–A04 (alçados), CT1–CT2 (cortes) e P04 (planta com nomes) com cotas documentadas.
- Imagens fixas com a porta de entrada fechada; no vídeo do percurso ela fica aberta (a câmera passa por ela).
- Corrigidos nesta versão: bica da torneira da ilha e vidro da máquina de lavar estavam abaixo do piso (posição aplicada em dobro).
- PDF profissional: `exports/apresentacao_casa.pdf` (23 pranchas A3), gerado por `scripts/pdf_apresentacao.sh`.
