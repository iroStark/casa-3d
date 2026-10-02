// Teste do build de produção: todo arquivo referenciado pelo site existe em dist/.
import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { GALERIA, PLANTAS, DOWNLOADS, CAPITULOS } from "../src/conteudo.js";

const dist = fileURLToPath(new URL("../dist/", import.meta.url));
const falhas = [];
const ok = (cond, msg) => { if (!cond) falhas.push(msg); };
const tem = (rel, min = 1) => {
  const p = join(dist, rel);
  ok(existsSync(p) && statSync(p).size >= min, `faltando ou vazio: ${rel}`);
};

tem("index.html");
const html = readFileSync(join(dist, "index.html"), "utf8");
ok(/<script type="module"[^>]+src="[^"]+\.js"/.test(html), "index.html sem script do bundle");
// termos privados do carimbo ficam numa lista local fora do repositório (source/termos_privados.txt)
const listaPriv = fileURLToPath(new URL("../../source/termos_privados.txt", import.meta.url));
const privados = existsSync(listaPriv) ? readFileSync(listaPriv, "utf8").split(/\r?\n/).filter(Boolean) : [];
const vaza = (txt) => privados.filter((t) => txt.toLowerCase().includes(t.toLowerCase()));
ok(vaza(html).length === 0, "dados do carimbo no HTML");
tem("modelo/casa.glb", 500_000);
tem("dados/percurso.json"); tem("dados/projeto.json");
tem("draco/draco_decoder.wasm"); tem("draco/draco_wasm_wrapper.js");
tem("video/visita.mp4", 1_000_000);
for (const g of GALERIA) { tem(`renders/web/${g.id}.jpg`, 10_000); tem(`renders/4k/${g.id}.jpg`, 100_000); }
for (const p of PLANTAS) tem(p.src, 10_000);
for (const c of CAPITULOS) tem(`renders/web/${c.img}.jpg`, 10_000);
for (const d of DOWNLOADS) if (!d.href.startsWith("http")) tem(d.href);
const perc = JSON.parse(readFileSync(join(dist, "dados/percurso.json"), "utf8"));
ok(perc.amostras.length > 200, "percurso curto demais");
const fim = CAPITULOS[CAPITULOS.length - 1].t1;
ok(Math.abs(fim - perc.duracao) < 0.01, `capítulos (${fim}s) e percurso (${perc.duracao}s) dessincronizados`);
const proj = readFileSync(join(dist, "dados/projeto.json"), "utf8");
ok(vaza(proj).length === 0, "dados do carimbo no projeto.json publicado");
import("node:fs").then(({ readdirSync }) => {
  for (const a of readdirSync(join(dist, "assets"))) if (a.endsWith(".js")) ok(vaza(readFileSync(join(dist, "assets", a), "utf8")).length === 0, `dados do carimbo em assets/${a}`);
  fim2();
});

function fim2() {
if (falhas.length) { console.error("FALHAS:\n - " + falhas.join("\n - ")); process.exit(1); }
console.log(`OK: ${GALERIA.length} imagens, ${PLANTAS.length} pranchas, GLB, vídeo, percurso e dados conferidos.`);
}
