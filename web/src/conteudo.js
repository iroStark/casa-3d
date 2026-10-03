// Textos e listas do site. Medidas citadas vêm do PDF do projeto (ver data/projeto.json).
// t0/t1 = trecho do percurso (segundos) que cada capítulo controla na rolagem.

export const CAPITULOS = [
  {
    id: "chegada", rotulo: "Chegada", t0: 0, t1: 9, img: "E01",
    titulo: "Primeiro, de longe",
    texto: [
      "Uma casa térrea, com uma laje plana que avança cerca de um metro além das paredes em todos os lados. Esse beiral faz sombra nas fachadas e protege quem chega da chuva.",
      "A garagem fica coberta pela mesma laje e aberta para o norte e para o leste: o carro entra sem portão de garagem e a casa continua leve."
    ],
    medida: "<b>Laje de cobertura:</b> 15,35 × 13,10 m · <b>Terreno:</b> 30 × 25 m",
  },
  {
    id: "entrada", rotulo: "Entrada", t0: 9, t1: 16.5, img: "V05",
    titulo: "A porta e o corredor",
    texto: [
      "Placas de concreto atravessam o jardim até a porta pivotante, embutida nos painéis da fachada. Ela abre para um corredor que distribui a casa: suítes de um lado, sala e cozinha do outro.",
      "É o lugar dos abraços de boas-vindas e das mochilas largadas no fim do dia."
    ],
    medida: "<b>Porta:</b> 1,00 m de largura · <b>Corredor:</b> 1,00 m · <b>Forro:</b> 3,05 m de altura",
  },
  {
    id: "suite1", rotulo: "Suíte 1", t0: 16.5, t1: 26.5, img: "S101",
    titulo: "O quarto para descansar",
    texto: [
      "A cama encosta na parede leste, como na planta mobiliada do projeto, de frente para o vidro do piso ao teto que dá para o jardim do lado sul.",
      "Cabeceira estofada grafite de parede inteira com luz indireta, armário em L, banheiro próprio ao lado e uma poltrona perto da janela para ler antes de dormir."
    ],
    medida: "<b>Largura:</b> 3,00 m · <b>Vão de vidro:</b> 3,00 × 2,90 m · <b>Banheiro:</b> 1,30 m de largura",
  },
  {
    id: "suite2", rotulo: "Suíte 2", t0: 26.5, t1: 37, img: "S201",
    titulo: "Um quarto com duas camas",
    texto: [
      "O projeto prevê duas camas de solteiro. Atrás delas, uma parede de réguas de madeira com luz indireta; almofadas salmão e uma penteadeira com espelho em arco.",
      "Serve para crianças, para visitas que ficam o fim de semana, ou para virar escritório um dia."
    ],
    medida: "<b>Largura:</b> 3,00 m · <b>Banheiro próprio:</b> 1,30 × 2,45 m",
  },
  {
    id: "estar", rotulo: "Sala de estar", t0: 37, t1: 42.5, img: "V07",
    titulo: "A sala que olha para a piscina",
    texto: [
      "A parede oeste é quase toda de vidro. À tarde, a luz entra baixa e dourada pela sala, e a piscina aparece logo ali fora.",
      "Sofá cinza modular com almofadas de couro e pied-de-poule, mesa de centro orgânica em nogueira e a TV num painel de madeira com luz no topo."
    ],
    medida: "<b>Largura:</b> 5,00 m · <b>Panos de vidro a oeste:</b> 2 × ~3,95 m, até 2,90 m de altura",
  },
  {
    id: "jantar", rotulo: "Jantar e cozinha", t0: 42.5, t1: 56, img: "K01",
    titulo: "O primeiro café, a família à mesa",
    texto: [
      "Cozinha e jantar dividem o mesmo espaço. Marcenaria terracota com geladeira inox, ilha em pedra com cooktop e cuba, trilho preto com pendentes; na mesa clara, cadeiras azuis e dois pendentes de palha.",
      "A mesa recebe oito pessoas. Ao lado, a despensa e um lavabo completam o apoio da cozinha."
    ],
    medida: "<b>Ilha:</b> 1,10 × 3,35 m · <b>Bancada:</b> 0,90 m · <b>Balcão:</b> 1,10 m (cortes)",
  },
  {
    id: "piscina", rotulo: "Piscina", t0: 56, t1: 66.5, img: "V02",
    titulo: "Quando os amigos chegarem",
    texto: [
      "Uma folha do vidro da sala de jantar corre e a casa se abre para o quintal. A piscina fica a poucos passos, com deck de madeira e espreguiçadeiras à sombra.",
      "É aqui que o domingo acontece."
    ],
    medida: "<b>Piscina:</b> 2,50 × 9,50 m (cotada na folha 02)",
  },
  {
    id: "despedida", rotulo: "Até logo", t0: 66.5, t1: 72.5, img: "E07",
    titulo: "Um começo",
    texto: [
      "Ainda é projeto, e isso é a melhor parte: tudo o que você viu pode ser ajustado antes da obra. Parabéns pela casa nova."
    ],
  },
];

export const GALERIA = [
  ["V05", "Exterior", "Fachada de entrada: painéis taupe, porta pivotante e placas-degrau"],
  ["V06", "Exterior", "Entrada e garagem"],
  ["V02", "Exterior", "Salas abertas para a piscina"],
  ["V03", "Exterior", "Piscina e salas"],
  ["V04", "Exterior", "Canto da área de serviço"],
  ["V07", "Sala", "Sala de estar com a piscina ao fundo"],
  ["V01", "Sala", "Jantar, sala e piscina — o enquadramento do vídeo de apresentação"],
  ["E01", "Exterior", "Fachada leste: entrada e garagem coberta"],
  ["E02", "Exterior", "Fachada norte e garagem aberta"],
  ["E03", "Exterior", "Fachada oeste e piscina"],
  ["E04", "Exterior", "Piscina e salas integradas"],
  ["E05", "Exterior", "Fachada sul, com as suítes"],
  ["E06", "Exterior", "Vista aérea a partir do nordeste"],
  ["E07", "Exterior", "Vista aérea a partir do sudoeste"],
  ["E08", "Exterior", "Cobertura vista de cima"],
  ["E09", "Entardecer", "Entrada ao entardecer"],
  ["E10", "Entardecer", "Piscina ao entardecer"],
  ["E11", "Entardecer", "Vista aérea ao entardecer"],
  ["E12", "Entardecer", "Fachada oeste ao entardecer"],
  ["I01", "Sala", "Sala de estar"],
  ["I02", "Sala", "Sala de estar, vista da janela"],
  ["I03", "Sala", "Sala de estar, vista da TV"],
  ["I04", "Sala", "Detalhe da mesa de centro"],
  ["D01", "Jantar e cozinha", "Sala de jantar"],
  ["D02", "Jantar e cozinha", "Jantar, cozinha e sala"],
  ["D03", "Jantar e cozinha", "Detalhe da mesa e dos pendentes"],
  ["K01", "Jantar e cozinha", "Cozinha: ilha e marcenaria do nicho"],
  ["K02", "Jantar e cozinha", "Cozinha vista da passagem da despensa"],
  ["K03", "Jantar e cozinha", "Detalhe da cuba e do misturador"],
  ["C01", "Circulação", "Corredor em direção à entrada"],
  ["C02", "Circulação", "Corredor visto da entrada"],
  ["S101", "Suítes", "Suíte 1"],
  ["S102", "Suítes", "Suíte 1, vista da janela"],
  ["S103", "Suítes", "Suíte 1, poltrona e janela"],
  ["S104", "Suítes", "Suíte 1, detalhe da cabeceira"],
  ["S201", "Suítes", "Suíte 2"],
  ["S202", "Suítes", "Suíte 2, vista da janela"],
  ["S203", "Suítes", "Suíte 2, penteadeira com espelho em arco"],
  ["B01", "Banheiros", "Banheiro da suíte 2 (vista com a parede cortada)"],
  ["B02", "Banheiros", "Banheiro da suíte 2, vista do corredor (parede cortada)"],
  ["B03", "Banheiros", "Banheiro da suíte 1 (vista com a parede cortada)"],
  ["B04", "Banheiros", "Banheiro da suíte 1, vista do jardim sul (parede cortada)"],
  ["B05", "Banheiros", "WC social (vista com a parede cortada)"],
  ["B06", "Banheiros", "WC social, vista lateral (parede cortada)"],
  ["X01", "Apoio", "Despensa (vista com a parede cortada)"],
  ["X02", "Apoio", "Despensa, vista da cozinha (parede cortada)"],
  ["X03", "Apoio", "Área de serviço"],
  ["X04", "Apoio", "Área de serviço, lateral"],
  ["X05", "Apoio", "Garagem"],
  ["X06", "Apoio", "Garagem, vista da abertura norte"],
  ["M01", "Detalhes", "Pendentes de palha sobre a mesa"],
  ["M02", "Detalhes", "Borda da piscina e deck"],
  ["M03", "Detalhes", "Parede de madeira iluminada da suíte 2"],
  ["P01", "Plantas 3D", "Planta 3D mobiliada"],
  ["P02", "Plantas 3D", "Planta 3D em perspectiva (sudeste)"],
  ["P03", "Plantas 3D", "Planta 3D em perspectiva (noroeste)"],
  ["P05", "Plantas 3D", "Implantação: planta humanizada cotada"],
  ["P04", "Plantas 3D", "Planta 3D com os nomes dos ambientes"],
  ["A01", "Alçados e cortes", "Alçado frontal — fachada leste"],
  ["A02", "Alçados e cortes", "Alçado lateral direito — fachada norte"],
  ["A03", "Alçados e cortes", "Alçado lateral esquerdo — fachada sul"],
  ["A04", "Alçados e cortes", "Alçado posterior — fachada oeste"],
  ["CT1", "Alçados e cortes", "Corte longitudinal 3D"],
  ["CT2", "Alçados e cortes", "Corte transversal 3D"],
].map(([id, grupo, legenda]) => ({ id, grupo, legenda }));

export const PLANTAS = [
  { src: "renders/web/P05.jpg", grande: "renders/4k/P05.jpg", tipo: "Modelo", legenda: "Implantação — planta humanizada cotada (medidas do projeto)" },
  { src: "renders/web/A01.jpg", grande: "renders/4k/A01.jpg", tipo: "Modelo", legenda: "Alçado frontal 3D (leste) com os níveis dos cortes" },
  { src: "renders/web/A02.jpg", grande: "renders/4k/A02.jpg", tipo: "Modelo", legenda: "Alçado lateral direito 3D (norte)" },
  { src: "renders/web/A03.jpg", grande: "renders/4k/A03.jpg", tipo: "Modelo", legenda: "Alçado lateral esquerdo 3D (sul)" },
  { src: "renders/web/A04.jpg", grande: "renders/4k/A04.jpg", tipo: "Modelo", legenda: "Alçado posterior 3D (oeste)" },
  { src: "renders/web/CT1.jpg", grande: "renders/4k/CT1.jpg", tipo: "Modelo", legenda: "Corte longitudinal 3D" },
  { src: "renders/web/CT2.jpg", grande: "renders/4k/CT2.jpg", tipo: "Modelo", legenda: "Corte transversal 3D" },
  { src: "renders/web/P04.jpg", grande: "renders/4k/P04.jpg", tipo: "Modelo", legenda: "Planta 3D com os nomes dos ambientes" },
  { src: "renders/web/P01.jpg", grande: "renders/4k/P01.jpg", tipo: "Modelo", legenda: "Planta 3D mobiliada gerada do modelo (paredes cortadas a 2,40 m)" },
  { src: "renders/web/P02.jpg", grande: "renders/4k/P02.jpg", tipo: "Modelo", legenda: "Planta 3D em perspectiva, sudeste" },
  { src: "renders/web/P03.jpg", grande: "renders/4k/P03.jpg", tipo: "Modelo", legenda: "Planta 3D em perspectiva, noroeste" },
  { src: "plantas/folha02_planta_cotas.jpg", tipo: "PDF", legenda: "Folha 02 — planta de distribuição e cotas (recorte do PDF)" },
  { src: "plantas/folha04_mobiliar.jpg", tipo: "PDF", legenda: "Folha 04 — planta mobiliada do projeto (base da ambientação)" },
  { src: "plantas/folha08_alcados.jpg", tipo: "PDF", legenda: "Folha 08 — fachadas (alçados)" },
  { src: "plantas/folha03_cortes.jpg", tipo: "PDF", legenda: "Folha 03 — cortes A/A e B/B (alturas)" },
  { src: "plantas/folha01_fundacao.jpg", tipo: "PDF", legenda: "Folha 01 — fundação, com os eixos usados como âncora" },
  { src: "plantas/validacao_overlay.jpg", tipo: "Conferência", legenda: "Conferência: corte do modelo a 1,50 m (vermelho) sobre a folha 02 (cinza)" },
];

export const DOWNLOADS = [
  { nome: "Apresentação completa (.pdf)", desc: "23 pranchas A3: implantação cotada, plantas 3D, alçados, cortes, fachadas e todos os ambientes.", href: "https://github.com/iroStark/casa-3d/releases/latest/download/apresentacao_casa.pdf", tam: "" },
  { nome: "Modelo Blender (.blend, texturas embutidas)", desc: "Arquivo editável com coleções, materiais, câmeras, luzes e o percurso animado. Blender 5.2.", href: "https://github.com/iroStark/casa-3d/releases/latest/download/casa_blender.zip", tam: "" },
  { nome: "Modelo web (.glb)", desc: "Versão otimizada usada nesta página (Draco + WebP).", href: "modelo/casa.glb", tam: "" },
  { nome: "Vídeo da visita (.mp4)", desc: "Animação renderizada a partir do modelo.", href: "video/visita.mp4", tam: "" },
  { nome: "Imagens em 4K (.zip)", desc: "Todas as imagens renderizadas em 3840 × 2160.", href: "https://github.com/iroStark/casa-3d/releases/latest/download/renders_4k.zip", tam: "" },
  { nome: "Modelo técnico IFC (.ifc)", desc: "Paredes, lajes, aberturas e espaços em formato aberto (ver limitações na seção de fidelidade).", href: "https://github.com/iroStark/casa-3d/releases/latest/download/casa.ifc", tam: "" },
  { nome: "Base de dados do projeto (.json)", desc: "Eixos, níveis, paredes, vãos e conflitos com a origem de cada número.", href: "dados/projeto.json", tam: "" },
  { nome: "Código-fonte e scripts", desc: "Tudo o que gera o modelo, as imagens, o vídeo e este site.", href: "https://github.com/iroStark/casa-3d", tam: "" },
];

export const FIDELIDADE = [
  {
    titulo: "Documentado no PDF e conferido",
    itens: [
      "Eixos estruturais da folha de fundação (5,20 / 3,20 / 1,50 / 3,20 m e 4,75 / 1,20 / 4,85 / 5,05 m) usados como âncora de toda a planta.",
      "Paredes de 0,20 m, larguras dos ambientes (5,00; 3,00; 1,30; 1,00 m) e posição das portas e do sentido de abertura.",
      "Alturas dos cortes: portas 2,10 m, vidros 2,90 m, forro 3,05 m, laje 3,20–3,40 m.",
      "Laje plana 15,35 × 13,10 m com caimento leve para as quatro bordas; piscina 2,50 × 9,50 m; lote 30 × 25 m.",
      "O corte do modelo a 1,50 m foi sobreposto à folha 02 para conferir paredes e vãos.",
    ],
  },
  {
    titulo: "Inferido ou adotado como hipótese",
    itens: [
      "Larguras dos panos de vidro da sala (≈3,95 m) medidas no desenho e nas fachadas: as cotas escritas (3,45 / 3,50 / 3,65) não fecham com os eixos.",
      "Eixo F (fachada sul das suítes) a 11,15 m do eixo A pelo desenho; a cota escrita indica 10,95 m.",
      "Altura da porta de entrada (2,90 m) lida na fachada; profundidade da piscina (1,40 m), muro (2,00 m) e caimento da laje (1%) não constam do PDF.",
      "Norte para o topo da prancha, como na imagem de apresentação do PDF; as folhas técnicas não têm seta de norte.",
    ],
  },
  {
    titulo: "Proposta de ambientação (não é projeto)",
    itens: [
      "Móveis, tecidos, cores, marcenaria, metais, iluminação decorativa, plantas, deck, espreguiçadeiras e árvores — posicionados a partir da planta mobiliada da folha 04.",
      "Estilo, cores e peças seguem o vídeo de apresentação do mesmo projeto (mesma marca d'água das imagens das págs. 26–28 do PDF): piso amadeirado claro, cadeiras azuis, pendentes de palha, sofá cinza em L, cabeceira grafite, muro verde, deck e piscina turquesa.",
      "Portão e acesso de veículos pelo leste, coerentes com a garagem aberta para esse lado.",
    ],
  },
  {
    titulo: "Pontos para o engenheiro validar",
    itens: [
      "Os três banheiros não mostram janela nem ventilação mecânica nas plantas.",
      "Cadeias de cotas que não somam o comprimento entre eixos (fachadas norte e oeste) e a cota D–F de 5,00 m.",
      "Rótulos dos cortes A/A e B/B trocados em relação às linhas de corte da planta mobiliada.",
      "O carimbo indica uma localidade diferente da mencionada no pedido; a ambientação seguiu o pedido, e o site não informa localização.",
    ],
  },
];

// pontos de vista do modo de exploração (coordenadas do Blender: x leste, y norte, z altura)
export const AMBIENTES_EXPLORAR = [
  { id: "fora", nome: "Vista geral", cam: [26, 14, 12], alvo: [6.5, -5.5, 1] },
  { id: "estar", nome: "Sala de estar", cam: [4.8, -5.4, 1.6], alvo: [2.0, -8.4, 1.0] },
  { id: "jantar", nome: "Jantar e cozinha", cam: [5.2, -4.4, 1.6], alvo: [2.0, -2.0, 1.0] },
  { id: "suite1", nome: "Suíte 1", cam: [10.5, -6.6, 1.6], alvo: [12.3, -9.2, 0.9] },
  { id: "suite2", nome: "Suíte 2", cam: [7.9, -6.6, 1.6], alvo: [5.8, -8.6, 0.9] },
  { id: "corredor", nome: "Corredor", cam: [12.6, -5.35, 1.6], alvo: [5.0, -5.35, 1.4] },
  { id: "garagem", nome: "Garagem", cam: [16, 3, 2.4], alvo: [10.8, -2.3, 1.0] },
  { id: "piscina", nome: "Piscina", cam: [-2.2, -12.5, 2.2], alvo: [-5.3, -4.8, 0] },
];
