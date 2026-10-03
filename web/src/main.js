import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { CAPITULOS, GALERIA, PLANTAS, DOWNLOADS, FIDELIDADE, AMBIENTES_EXPLORAR } from "./conteudo.js";

const BASE = import.meta.env.BASE_URL;
const $ = (s) => document.querySelector(s);
const reduzMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const ehMovel = window.matchMedia("(max-width: 760px)").matches || "ontouchstart" in window;

/* ------------------------------------------------------------------ conteúdo */
function montarCapitulos() {
  const box = $("#capitulos");
  const indice = $("#indiceAmbientes");
  CAPITULOS.forEach((c, i) => {
    const s = document.createElement("section");
    s.className = "capitulo";
    s.id = "cap-" + c.id;
    s.dataset.t0 = c.t0; s.dataset.t1 = c.t1;
    s.setAttribute("aria-labelledby", "tit-" + c.id);
    s.innerHTML = `<div class="cartao">
        <span class="num">${String(i + 1).padStart(2, "0")} · ${c.rotulo}</span>
        <h3 id="tit-${c.id}">${c.titulo}</h3>
        ${c.texto.map((p) => `<p>${p}</p>`).join("")}
        ${c.medida ? `<p class="medida">${c.medida}</p>` : ""}
      </div>`;
    box.appendChild(s);
    const li = document.createElement("li");
    li.innerHTML = `<button type="button" data-alvo="cap-${c.id}">${c.rotulo}</button>`;
    indice.appendChild(li);
  });
  indice.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-alvo]");
    if (!b) return;
    const el = document.getElementById(b.dataset.alvo);
    const y = el.getBoundingClientRect().top + window.scrollY + el.offsetHeight * 0.3;
    window.scrollTo({ top: y, behavior: reduzMovimento ? "auto" : "smooth" });
  });
  // altura do cartão (posição fixa na parte de baixo, no celular)
  const medir = () => document.querySelectorAll(".capitulo .cartao").forEach((c) => c.style.setProperty("--card-h", c.offsetHeight + "px"));
  medir(); window.addEventListener("resize", medir);
}

let galeriaAtual = [];
function montarGaleria() {
  const filtros = $("#filtrosGaleria");
  const grupos = ["Todos", ...new Set(GALERIA.map((g) => g.grupo))];
  grupos.forEach((g, i) => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = g; b.setAttribute("aria-pressed", i === 0 ? "true" : "false");
    b.addEventListener("click", () => {
      filtros.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      desenhar(g);
    });
    filtros.appendChild(b);
  });
  const ul = $("#galeria");
  function desenhar(g) {
    galeriaAtual = GALERIA.filter((x) => g === "Todos" || x.grupo === g);
    ul.innerHTML = galeriaAtual.map((x, i) => `<li><button type="button" data-i="${i}" aria-label="Ampliar: ${x.legenda}">
      <img loading="lazy" src="${BASE}renders/web/${x.id}.jpg" alt="${x.legenda}" width="960" height="540" />
      <span class="leg">${x.legenda}</span></button></li>`).join("");
  }
  desenhar("Todos");
  ul.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-i]");
    if (b) abrirCaixa(galeriaAtual, +b.dataset.i, (x) => `${BASE}renders/4k/${x.id}.jpg`);
  });
}

function montarPlantas() {
  const g = $("#plantasGrade");
  g.innerHTML = PLANTAS.map((p, i) => `<figure>
    <img loading="lazy" src="${BASE}${p.src}" alt="${p.legenda}" data-i="${i}" tabindex="0" role="button" aria-label="Ampliar: ${p.legenda}" />
    <figcaption><span class="selo ${p.tipo === "PDF" ? "doc" : ""}">${p.tipo}</span>${p.legenda}</figcaption></figure>`).join("");
  const abrir = (el) => abrirCaixa(PLANTAS, +el.dataset.i, (x) => BASE + (x.grande || x.src));
  g.addEventListener("click", (e) => { const im = e.target.closest("img[data-i]"); if (im) abrir(im); });
  g.addEventListener("keydown", (e) => { const im = e.target.closest("img[data-i]"); if (im && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); abrir(im); } });
}

function montarDownloads() {
  $("#downloads").innerHTML = DOWNLOADS.map((d) => `<li><div class="info"><b>${d.nome}</b><small>${d.desc}</small></div>
    <a class="btn" href="${d.href.startsWith("http") ? d.href : BASE + d.href}" ${d.href.startsWith("http") ? 'rel="noopener"' : "download"}>Baixar${d.tam ? " · " + d.tam : ""}</a></li>`).join("");
  $("#listaFidelidade").innerHTML = FIDELIDADE.map((b) => `<h3>${b.titulo}</h3><ul class="fid-lista">${b.itens.map((i) => `<li>${i}</li>`).join("")}</ul>`).join("");
}

/* ------------------------------------------------------------------ lightbox */
const caixa = $("#caixaImagem");
let cxLista = [], cxI = 0, cxSrc = null, cxOrigem = null;
function abrirCaixa(lista, i, src) {
  cxLista = lista; cxI = i; cxSrc = src; cxOrigem = document.activeElement;
  mostrarCaixa(); caixa.showModal();
}
function mostrarCaixa() {
  const x = cxLista[cxI];
  $("#caixaImg").src = cxSrc(x); $("#caixaImg").alt = x.legenda; $("#caixaLegenda").textContent = x.legenda;
}
$("#caixaFechar").addEventListener("click", () => caixa.close());
$("#caixaAnterior").addEventListener("click", () => { cxI = (cxI - 1 + cxLista.length) % cxLista.length; mostrarCaixa(); });
$("#caixaProxima").addEventListener("click", () => { cxI = (cxI + 1) % cxLista.length; mostrarCaixa(); });
caixa.addEventListener("close", () => cxOrigem && cxOrigem.focus && cxOrigem.focus());
caixa.addEventListener("click", (e) => { if (e.target === caixa) caixa.close(); });
caixa.addEventListener("keydown", (e) => { if (e.key === "ArrowLeft") $("#caixaAnterior").click(); if (e.key === "ArrowRight") $("#caixaProxima").click(); });

/* ------------------------------------------------------------------ menu móvel */
const menu = $("#menuMovel"), btnMenu = $("#btnMenu");
function fecharMenu() { menu.hidden = true; btnMenu.setAttribute("aria-expanded", "false"); btnMenu.setAttribute("aria-label", "Abrir menu"); }
btnMenu.addEventListener("click", () => {
  const abrir = menu.hidden;
  menu.hidden = !abrir; btnMenu.setAttribute("aria-expanded", String(abrir)); btnMenu.setAttribute("aria-label", abrir ? "Fechar menu" : "Abrir menu");
  if (abrir) menu.querySelector("a").focus();
});
$("#btnFecharMenu").addEventListener("click", () => { fecharMenu(); btnMenu.focus(); });
menu.addEventListener("click", (e) => { if (e.target.closest("a")) fecharMenu(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !menu.hidden) { fecharMenu(); btnMenu.focus(); } });

/* ------------------------------------------------------------------ 3D */
const canvas = $("#cena");
let renderer, scene, camera, controls, percurso, modelo;
let cobertura = [], forros = [];
let modo = "visita"; // visita | explorar
let tAlvo = 0, tAtual = 0;
const tmpP = new THREE.Vector3(), tmpA = new THREE.Vector3();
const b2t = (v) => new THREE.Vector3(v[0], v[2], -v[1]); // Blender Z-up -> three Y-up

function fallback(msg) {
  const img = $("#palcoFallback");
  img.src = `${BASE}renders/web/E01.jpg`; img.hidden = false;
  const c = $("#carregando");
  c.classList.add("erro"); c.hidden = false;
  $("#textoCarregando").textContent = msg;
  $("#barraProgresso").style.width = "100%";
  document.body.classList.add("sem3d");
  CAPITULOS.forEach((cap) => { const s = document.getElementById("cap-" + cap.id); if (s) s.dataset.img = cap.img; });
  setTimeout(() => (c.hidden = true), 7000);
}

function webglOk() {
  try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); } catch { return false; }
}

async function iniciar3D() {
  if (!webglOk()) return fallback("Este navegador não exibe 3D. Mostrando as imagens renderizadas.");
  renderer = new THREE.WebGLRenderer({ canvas, antialias: !ehMovel, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, ehMovel ? 1.5 : 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = !ehMovel;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0xcfd9e2);
  scene.fog = new THREE.Fog(0xcfd9e2, 60, 160);
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.55;
  camera = new THREE.PerspectiveCamera(55, 1, 0.05, 500);
  scene.add(new THREE.HemisphereLight(0xeaf2ff, 0x8a7a62, 0.9));
  const sol = new THREE.DirectionalLight(0xfff1dc, 2.6);
  sol.position.set(-22, 30, -14); // noroeste, tarde
  sol.castShadow = !ehMovel;
  sol.shadow.mapSize.set(2048, 2048);
  Object.assign(sol.shadow.camera, { left: -26, right: 26, top: 26, bottom: -26, near: 1, far: 90 });
  sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.03;
  sol.target.position.set(6.5, 0, 5.5);
  scene.add(sol, sol.target);
  // luz interna suave (os renders têm a iluminação completa; aqui só preenche os ambientes)
  const interna = new THREE.PointLight(0xffd7a8, 18, 9, 1.6); interna.position.set(3, 2.6, 5); scene.add(interna);
  const interna2 = new THREE.PointLight(0xffd7a8, 14, 8, 1.6); interna2.position.set(9.5, 2.6, 8.4); scene.add(interna2);
  const interna3 = new THREE.PointLight(0xffd7a8, 10, 8, 1.6); interna3.position.set(9.5, 2.6, 5.3); scene.add(interna3);

  controls = new OrbitControls(camera, canvas);
  controls.enabled = false; controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.maxPolarAngle = Math.PI * 0.495; controls.minDistance = 0.4; controls.maxDistance = 90;
  controls.listenToKeyEvents(window);

  const [dados] = await Promise.all([fetch(`${BASE}dados/percurso.json`).then((r) => r.json())]);
  percurso = dados.amostras.map((a) => ({ t: a.t, p: b2t(a.p), a: b2t(a.a), amb: a.amb }));

  const draco = new DRACOLoader(); draco.setDecoderPath(`${BASE}draco/`);
  const loader = new GLTFLoader(); loader.setDRACOLoader(draco);
  const barra = $("#barraProgresso");
  const gltf = await new Promise((res, rej) => loader.load(`${BASE}modelo/casa.glb`, res,
    (e) => { if (e.total) barra.style.width = Math.round((e.loaded / e.total) * 100) + "%"; }, rej));
  modelo = gltf.scene;
  modelo.traverse((o) => {
    if (!o.isMesh) return;
    const nome = (o.parent && o.parent.name) || o.name;
    const raiz = nomeRaiz(o);
    o.castShadow = !ehMovel && raiz !== "WEB_Vegetacao";
    o.receiveShadow = !ehMovel;
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    mats.forEach((m) => {
      if (m.userData && m.userData.web_vidro) {
        m.transparent = true; m.opacity = 0.16; m.transmission = 0; m.roughness = 0.05; m.metalness = 0; m.depthWrite = false;
        m.color = new THREE.Color(0xdfeeee);
      }
      if (m.map && m.alphaMap === null && m.transparent && /Folhagem|Flor|Arbusto/.test(m.name)) { m.alphaTest = 0.5; m.transparent = false; m.side = THREE.DoubleSide; }
      if (/Folhagem|Flor|voil|Cortina|Voil/i.test(m.name)) m.side = THREE.DoubleSide;
      if (m.emissiveIntensity !== undefined && m.emissive && m.emissive.getHex() !== 0) m.emissiveIntensity = Math.min(m.emissiveIntensity, 2.5);
    });
    if (raiz === "WEB_Cobertura") cobertura.push(o);
    if (raiz === "WEB_Forros") forros.push(o);
  });
  scene.add(modelo);
  $("#carregando").hidden = true;
  const poster = $("#palcoFallback");
  poster.style.opacity = "0"; setTimeout(() => (poster.hidden = true), 700);
  redimensionar();
  aplicarTempo(0, true);
  renderer.setAnimationLoop(quadro);
}

function nomeRaiz(o) {
  let x = o;
  while (x.parent && x.parent !== modelo && x.parent.type !== "Scene") x = x.parent;
  return x.name;
}

function amostra(t) {
  const n = percurso.length;
  if (t <= 0) return [percurso[0].p, percurso[0].a];
  const dt = percurso[1].t - percurso[0].t;
  const f = Math.min(t / dt, n - 1.0001);
  const i = Math.floor(f), u = f - i;
  tmpP.lerpVectors(percurso[i].p, percurso[i + 1].p, u);
  tmpA.lerpVectors(percurso[i].a, percurso[i + 1].a, u);
  return [tmpP, tmpA];
}

function aplicarTempo(t, imediato) {
  const [p, a] = amostra(t);
  camera.position.copy(p);
  camera.lookAt(a);
  const dentro = t > 12.5 && t < 56.5;
  // a laje e o forro somem no voo de chegada (vista aérea) e reaparecem ao entrar
  const mostrarTeto = t > 7;
  cobertura.forEach((o) => (o.visible = mostrarTeto || modo === "explorar" ? !coberturaAberta : true));
  forros.forEach((o) => (o.visible = !coberturaAberta));
  renderer.toneMappingExposure = dentro ? 1.05 : 1.0;
}

let coberturaAberta = false;
function definirCobertura(aberta) {
  coberturaAberta = aberta;
  cobertura.forEach((o) => (o.visible = !aberta));
  forros.forEach((o) => (o.visible = !aberta));
  $("#btnCobertura").setAttribute("aria-pressed", String(aberta));
  $("#btnCobertura").textContent = aberta ? "Fechar cobertura" : "Abrir cobertura";
}

function redimensionar() {
  if (!renderer) return;
  const w = window.innerWidth, h = window.innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  // mantém ~78° de campo horizontal na visita (lente de 20 mm do Blender), limitado no retrato
  const hfov = 78 * Math.PI / 180;
  // na visita, o centro da cena sai de trás dos cartões: sobe no celular, vai à direita no desktop
  let fw = w, fh = h, ox = 0, oy = 0;
  if (modo === "visita") {
    if (w < 760) { fh = h * 1.34; oy = fh - h; }
    else { const d = Math.min(440, w * 0.3); fw = w + d; ox = 0; }
  }
  const asp = fw / fh;
  const v = 2 * Math.atan(Math.tan(hfov / 2) / asp) * 180 / Math.PI;
  camera.fov = Math.min(Math.max(v, 45), 92);
  if (fw !== w || fh !== h) camera.setViewOffset(fw, fh, ox, oy, w, h);
  else camera.clearViewOffset();
  camera.aspect = asp;
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", redimensionar);
if (window.visualViewport) window.visualViewport.addEventListener("resize", redimensionar);

/* tempo da visita a partir da rolagem */
function tempoDaRolagem() {
  const vis = $("#visita");
  const caps = [...document.querySelectorAll(".capitulo")];
  const meio = window.innerHeight * 0.5;
  let t = 0, ativo = null;
  const ini = $("#inicio").getBoundingClientRect();
  if (ini.bottom > meio) {
    // ainda na abertura: voo aéreo inicial (0–5 s) conforme sai da abertura
    const fr = 1 - Math.max(0, Math.min(1, (ini.bottom - meio) / (window.innerHeight * 0.5)));
    return { t: fr * 2.0, ativo: null };
  }
  for (const c of caps) {
    const r = c.getBoundingClientRect();
    if (r.top <= meio && r.bottom > meio) {
      const fr = (meio - r.top) / r.height;
      const t0 = +c.dataset.t0, t1 = +c.dataset.t1;
      t = reduzMovimento ? (t0 + t1) / 2 : t0 + (t1 - t0) * fr;
      ativo = c;
      break;
    }
    if (r.bottom <= meio) t = +c.dataset.t1;
  }
  return { t, ativo };
}

let ultimoAtivo = null;
function aoRolar() {
  if (modo !== "visita") return;
  const { t, ativo } = tempoDaRolagem();
  tAlvo = t;
  if (ativo !== ultimoAtivo) {
    document.querySelectorAll(".capitulo").forEach((c) => c.classList.toggle("ativo", c === ativo));
    document.querySelectorAll("#indiceAmbientes button").forEach((b) => b.setAttribute("aria-current", String(ativo && b.dataset.alvo === ativo.id)));
    ultimoAtivo = ativo;
    if (document.body.classList.contains("sem3d") && ativo && ativo.dataset.img) {
      const img = $("#palcoFallback"); img.src = `${BASE}renders/web/${ativo.dataset.img}.jpg`;
    }
  }
}
window.addEventListener("scroll", aoRolar, { passive: true });

let ultimoQuadro = performance.now();
function quadro() {
  const agora = performance.now();
  const dt = Math.min(0.1, (agora - ultimoQuadro) / 1000); ultimoQuadro = agora;
  if (modo === "visita") {
    // suavização dependente do tempo (igual em 30 ou 120 fps); acompanha a rolagem em ~0,4 s
    const k = reduzMovimento ? 1 : 1 - Math.exp(-dt * 7);
    tAtual += (tAlvo - tAtual) * k;
    if (Math.abs(tAlvo - tAtual) < 1e-4) tAtual = tAlvo;
    aplicarTempo(tAtual);
  } else {
    controls.update();
  }
  renderer.render(scene, camera);
}

/* ------------------------------------------------------------------ exploração livre */
function entrarExplorar(op = {}) {
  if (!renderer) return;
  modo = "explorar";
  document.body.classList.add("explorando");
  $("#explorarBarra").hidden = false;
  controls.enabled = true;
  redimensionar();
  if (op.superior) vistaSuperior(true);
  else {
    const [p, a] = amostra(tAtual);
    controls.target.copy(a);
    camera.position.copy(p);
  }
  if (op.abrir) definirCobertura(true);
  $("#btnVoltarVisita").focus();
}
function sairExplorar() {
  modo = "visita";
  document.body.classList.remove("explorando");
  $("#explorarBarra").hidden = true;
  controls.enabled = false;
  definirCobertura(false);
  vistaSuperiorAtiva = false; $("#btnVistaSuperior").setAttribute("aria-pressed", "false");
  redimensionar();
  aoRolar();
  tAtual = tAlvo;
  $("#btnExplorar").focus({ preventScroll: true });
}
let vistaSuperiorAtiva = false;
function vistaSuperior(on) {
  vistaSuperiorAtiva = on;
  $("#btnVistaSuperior").setAttribute("aria-pressed", String(on));
  if (on) {
    controls.target.set(6.55, 0, 5.5);
    camera.position.set(6.55 + 0.01, 30, 5.5 + 14);
    definirCobertura(true);
  } else {
    controls.target.set(6.55, 1, 5.5);
    camera.position.set(24, 12, 22);
  }
}
function irPara(id) {
  const a = AMBIENTES_EXPLORAR.find((x) => x.id === id);
  if (!a) return;
  controls.target.copy(b2t(a.alvo));
  camera.position.copy(b2t(a.cam));
}

$("#btnExplorar").addEventListener("click", () => entrarExplorar());
$("#btnAbrirCima").addEventListener("click", () => entrarExplorar({ superior: true, abrir: true }));
$("#btnVoltarVisita").addEventListener("click", sairExplorar);
$("#btnVistaSuperior").addEventListener("click", () => vistaSuperior(!vistaSuperiorAtiva));
$("#btnCobertura").addEventListener("click", () => definirCobertura(!coberturaAberta));
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && modo === "explorar" && !caixa.open) sairExplorar(); });
const sel = $("#selAmbiente");
sel.innerHTML = `<option value="">Ir para…</option>` + AMBIENTES_EXPLORAR.map((a) => `<option value="${a.id}">${a.nome}</option>`).join("");
sel.addEventListener("change", () => { if (sel.value) irPara(sel.value); sel.value = ""; });

$("#btnVerModerna").addEventListener("click", () => {
  const b = [...document.querySelectorAll("#filtrosGaleria button")].find((x) => x.textContent === "Alçados e cortes");
  if (b) b.click();
  document.getElementById("ambientes").scrollIntoView({ behavior: reduzMovimento ? "auto" : "smooth" });
});

/* ------------------------------------------------------------------ início */
// imagem renderizada enquanto o modelo 3D carrega (e como alternativa se falhar)
{ const p = $("#palcoFallback"); p.src = `${BASE}renders/web/E06.jpg`; p.hidden = false; }
montarCapitulos();
montarGaleria();
montarPlantas();
montarDownloads();
aoRolar();
iniciar3D().catch((e) => { console.error(e); fallback("Não foi possível carregar o modelo 3D. Mostrando as imagens renderizadas."); });
