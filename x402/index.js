// Verdix x402 — endpoint berbayar (USDC di Base) di atas Verdix Reputation API.
// Caller (manusia/agent) bayar per-request via protokol x402; tanpa akun/API key.
// Publik: https://verdix-api.kilatlab.com/x402/...  (nginx → 127.0.0.1:8402)
// PAY_TO wajib diisi (alamat wallet awal) — tanpa itu route berbayar balas 503.

const express = require("express");
const { paymentMiddleware } = require("@x402/express");
const { x402ResourceServer, HTTPFacilitatorClient } = require("@x402/core/server");
const { ExactEvmScheme } = require("@x402/evm/exact/server");
const { declareDiscoveryExtension } = require("@x402/extensions");
const { SERVICES } = require("./services");
const data = require("./data");
const ta = require("./ta");
const tools = require("./tools");
const { marked } = require("marked");

const PAY_TO = process.env.X402_PAY_TO || "";
const PORT = parseInt(process.env.X402_PORT || "8402", 10);
const UPSTREAM = process.env.VERDIX_API || "http://127.0.0.1:8600";
// Default Base Sepolia (facilitator publik x402.org). Mainnet (eip155:8453)
// butuh facilitator CDP Coinbase + API key → set X402_NETWORK + X402_FACILITATOR.
const NETWORK = process.env.X402_NETWORK || "eip155:84532";
const FACILITATOR = process.env.X402_FACILITATOR || "https://x402.org/facilitator";

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "12mb" }));

// Katalog servis (harga/deskripsi/grup) ada di services.js — 4 bidang, 20 servis.

// ---------- x402 middleware ----------
if (PAY_TO) {
  const facilitator = new HTTPFacilitatorClient({ url: FACILITATOR });
  const server = new x402ResourceServer(facilitator);
  server.register(NETWORK, new ExactEvmScheme());
  const routes = {};
  for (const [route, s] of Object.entries(SERVICES)) {
    routes[route] = {
      accepts: { scheme: "exact", price: s.price, network: NETWORK, payTo: PAY_TO },
      description: s.desc,
      mimeType: s.mime,
      // discovery extension Bazaar cuma valid utk GET
      ...(route.startsWith("GET ")
        ? { extensions: { ...declareDiscoveryExtension({ output: { example: s.example } }) } }
        : {}),
    };
  }
  app.use(paymentMiddleware(routes, server));
} else {
  app.use("/x402", (req, res, next) => {
    if (req.path === "/" || req.path === "" || req.path === "/health") return next();
    res.status(503).json({ error: "payment address not configured yet — service warming up" });
  });
}

// ---------- helper proxy ke Verdix API ----------
async function upstreamJson(path, res, mime) {
  try {
    const r = await fetch(UPSTREAM + path, { headers: { Accept: "application/json" } });
    const body = await r.text();
    res.status(r.status).type(mime || r.headers.get("content-type") || "application/json").send(body);
  } catch (e) {
    res.status(502).json({ error: "upstream unavailable", detail: String(e.message || e) });
  }
}

// ---------- routes ----------
const GROUP_OF = (route) => route.includes("/market/") ? "Market Intelligence"
  : route.includes("/whale/") ? "Whale Intelligence"
  : route.includes("/ai/") ? "AI Analysis" : "Agent Trust";

function catalogHtml() {
  const groups = {};
  for (const [k, s] of Object.entries(SERVICES)) {
    const g = s.group || GROUP_OF(k);
    (groups[g] = groups[g] || []).push([k.replace("GET ", ""), s]);
  }
  const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  let cards = "";
  for (const [g, items] of Object.entries(groups)) {
    const rows = items.map(([p, s]) =>
      `<tr><td class="mono">${esc(p)}</td><td class="price">${esc(s.price)}</td><td>${esc(s.desc)}</td></tr>`).join("");
    cards += `<h2>${esc(g)} <span class="cnt">${items.length} services</span></h2>
      <div class="card"><div class="tblwrap"><table>
      <tr><th>Endpoint</th><th>Price</th><th>What you get</th></tr>${rows}</table></div></div>`;
  }
  return `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verdix x402 — pay-per-call trust &amp; market data for AI agents</title>
<meta name="description" content="Machine-payable data services: AI agents pay per call in USDC via the x402 protocol. No account, no API key.">
<style>
:root{color-scheme:dark}*{box-sizing:border-box;margin:0;padding:0}
body{background:#07090f;color:#e8ecf4;font:15px/1.65 'Space Grotesk',ui-sans-serif,system-ui,sans-serif;max-width:1080px;margin:0 auto;padding:48px 24px}
@font-face{font-family:'Space Grotesk';src:url('https://verdix.pages.dev/fonts/space-grotesk-var.woff2') format('woff2');font-weight:300 700;font-display:swap}
@font-face{font-family:'IBM Plex Mono';src:url('https://verdix.pages.dev/fonts/plex-mono-400.woff2') format('woff2');font-weight:400;font-display:swap}
a{color:#7aa2ff;text-decoration:none}a:hover{color:#a5c0ff}
h1{font-size:clamp(26px,4vw,34px);font-weight:700;background:linear-gradient(90deg,#e8ecf4,#22c97f 55%,#7aa2ff);-webkit-background-clip:text;background-clip:text;color:transparent}
h2{font-size:18px;margin:26px 0 8px;color:#cdd6e4}
.cnt{font:600 11px 'IBM Plex Mono',monospace;color:#6b7488;letter-spacing:.08em;text-transform:uppercase;margin-left:8px}
.sub{color:#9aa4b8;margin:6px 0 4px}
.badge{display:inline-block;padding:3px 12px;border-radius:99px;font:600 12px 'IBM Plex Mono',monospace;background:rgba(34,201,127,.1);color:#22c97f;border:1px solid rgba(34,201,127,.35);margin-bottom:14px}
.card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:16px 18px;margin:10px 0}
table{width:100%;border-collapse:collapse;min-width:560px}
th{color:#6b7488;text-align:left;font:600 11px 'IBM Plex Mono',monospace;text-transform:uppercase;letter-spacing:.08em;padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08)}
td{padding:9px 10px;border-bottom:1px solid rgba(255,255,255,.05);vertical-align:top}
.mono{font-family:'IBM Plex Mono',monospace;font-size:12.5px;white-space:nowrap}
.price{font-family:'IBM Plex Mono',monospace;color:#22c97f;font-weight:600;white-space:nowrap}
.tblwrap{overflow-x:auto}
.code{background:rgba(10,14,24,.8);border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:13px;font:12.5px 'IBM Plex Mono',monospace;color:#a5c0ff;overflow-x:auto;white-space:pre;margin:10px 0}
.foot{color:#6b7488;font-size:12px;margin-top:32px;border-top:1px solid rgba(255,255,255,.08);padding-top:14px}
</style></head><body>
<span class="badge">● x402 PROTOCOL — MACHINE-PAYABLE</span>
<h1>Verdix x402 Services</h1>
<p class="sub">Pay-per-call data for AI agents: USDC per request, no account, no API key.
Call an endpoint → get <span class="mono">HTTP 402</span> with payment requirements → pay → data.
Discoverable on the x402 Bazaar.</p>
<div class="code">npx awal x402 details https://verdix-api.kilatlab.com/x402/agent/1
npx awal x402 pay     https://verdix-api.kilatlab.com/x402/agent/1</div>
${cards}
<p class="sub">Free: <a href="/x402/health">/x402/health</a> · machine-readable catalog: <span class="mono">Accept: application/json</span> · docs: <a href="https://verdix.pages.dev/web/api">verdix.pages.dev/web/api</a></p>
<p class="foot">Verdix — verifiable economic memory for AI agents · data services, not investment advice · <a href="https://verdix.pages.dev/">verdix.pages.dev</a> · <a href="https://x.com/reyykanin">@reyykanin</a></p>
</body></html>`;
}

app.get("/x402/", (req, res) => {
  const wantsHtml = (req.headers.accept || "").includes("text/html");
  if (wantsHtml) return res.type("text/html").send(catalogHtml());
  res.json({
    service: "Verdix x402 — pay-per-call trust data for AI agents",
    how: "x402 protocol: call an endpoint, get HTTP 402 with payment requirements, pay USDC on Base, retry. Agent-native: `npx awal x402 pay <url>`.",
    network: NETWORK,
    endpoints: Object.fromEntries(Object.entries(SERVICES).map(([k, s]) => [k.replace("GET ", ""), { price: s.price, description: s.desc }])),
    free_tier: "same data, no SLA: https://verdix-api.kilatlab.com/",
    docs: "https://verdix.pages.dev/web/api",
  });
});
app.get("/x402/health", async (req, res) => {
  let up = false;
  try { up = (await fetch(UPSTREAM + "/agents", { headers: { Accept: "application/json" } })).ok; } catch {}
  res.json({ ok: true, upstream: up, paid_routes: Boolean(PAY_TO) });
});

app.get("/x402/agents", (req, res) => upstreamJson("/agents", res, "application/json"));
app.get("/x402/agent/:id", (req, res) => upstreamJson(`/agent/${req.params.id}`, res, "application/json"));
app.get("/x402/agent/:id/cv", (req, res) => upstreamJson(`/agent/${req.params.id}/cv`, res, "text/markdown"));
app.get("/x402/entries", (req, res) => upstreamJson("/entries", res, "application/json"));
app.get("/x402/bitagent", (req, res) => upstreamJson("/bitagent", res, "application/json"));
app.get("/x402/bitagent/:handle", (req, res) => upstreamJson(`/bitagent/${encodeURIComponent(req.params.handle)}`, res, "application/json"));
app.get("/x402/memory/:hash", (req, res) => upstreamJson(`/memory/${encodeURIComponent(req.params.hash)}`, res, "application/json"));

app.get("/x402/dossier/:id", async (req, res) => {
  const id = req.params.id;
  try {
    const get = (p, accept) => fetch(UPSTREAM + p, { headers: { Accept: accept || "application/json" } })
      .then((r) => (r.ok ? (accept === "text/plain" ? r.text() : r.json()) : null)).catch(() => null);
    const [profile, entries, cv] = await Promise.all([
      get(`/agent/${id}`), get("/entries"), get(`/agent/${id}/cv`, "text/plain"),
    ]);
    if (!profile) return res.status(404).json({ error: "agent not found" });
    res.json({ generated_at: new Date().toISOString(), agent_id: Number(id), profile, recent_entries: entries, economic_cv: cv });
  } catch (e) {
    res.status(502).json({ error: "upstream unavailable", detail: String(e.message || e) });
  }
});

// ---------- Bidang 2: Market Intelligence ----------
function symOr400(req, res) {
  const s = String(req.params.symbol || "").toUpperCase();
  if (!data.SYM_RE.test(s)) { res.status(400).json({ error: "bad symbol" }); return null; }
  return s;
}
app.get("/x402/market/funding/:symbol", (req, res) => {
  const s = symOr400(req, res); if (!s) return;
  res.json(data.funding(s, data.clampDays(req.query.days, 30, 365)));
});
app.get("/x402/market/oi-lsr/:symbol", (req, res) => {
  const s = symOr400(req, res); if (!s) return;
  res.json(data.oiLsr(s, data.clampDays(req.query.days, 7, 90)));
});
app.get("/x402/market/basis/:symbol", (req, res) => {
  const s = symOr400(req, res); if (!s) return;
  res.json(data.basis(s, data.clampDays(req.query.days, 30, 365)));
});
app.get("/x402/market/cot", (req, res) => res.json(data.cot()));
app.get("/x402/market/sentiment", (req, res) => res.json(data.sentiment()));
app.get("/x402/market/live/:symbol", async (req, res) => {
  const s = symOr400(req, res); if (!s) return;
  try { res.json(await data.liveMarket(s)); }
  catch (e) { res.status(502).json({ error: String(e.message || e) }); }
});

// ---------- Bidang 3: Whale Intelligence ----------
app.get("/x402/whale/bursts", (req, res) => res.json(data.bursts()));
app.get("/x402/whale/leaderboard", (req, res) => res.json(data.leaderboard()));
app.get("/x402/whale/wallet/:addr", (req, res) => {
  const a = String(req.params.addr || "");
  if (!data.ADDR_RE.test(a)) return res.status(400).json({ error: "bad address" });
  const info = data.walletInfo(a);
  if (!info) return res.status(404).json({ error: "wallet not in tracked cohort" });
  res.json(info);
});
app.get("/x402/whale/positions/:coin", (req, res) => {
  const c = String(req.params.coin || "").toUpperCase();
  if (!data.SYM_RE.test(c)) return res.status(400).json({ error: "bad coin" });
  res.json(data.coinPositions(c));
});

// ---------- Bidang 4: AI Analysis ----------
function aiGate(res) {
  if (!data.aiEnabled()) { res.status(503).json({ error: "AI tier not configured" }); return false; }
  if (!data.aiRateOk()) { res.status(429).json({ error: "AI tier rate limit — retry in a few minutes" }); return false; }
  return true;
}
app.get("/x402/ai/agent-audit/:id", async (req, res) => {
  if (!aiGate(res)) return;
  const id = req.params.id;
  try {
    const get = (p, accept) => fetch(UPSTREAM + p, { headers: { Accept: accept || "application/json" } })
      .then((r) => (r.ok ? (accept === "text/plain" ? r.text() : r.json()) : null)).catch(() => null);
    const [profile, entries, cv] = await Promise.all([
      get(`/agent/${id}`), get("/entries"), get(`/agent/${id}/cv`, "text/plain"),
    ]);
    if (!profile) return res.status(404).json({ error: "agent not found" });
    res.json(await data.agentAudit(id, { profile, recent_entries: entries, economic_cv: cv }));
  } catch (e) { res.status(502).json({ error: String(e.message || e) }); }
});
app.get("/x402/ai/market-brief/:symbol", async (req, res) => {
  if (!aiGate(res)) return;
  const s = symOr400(req, res); if (!s) return;
  try {
    const coin = s.replace(/USDT$|USDC$|USD$/, "");
    const [live, senti, wp] = await Promise.all([
      data.liveMarket(s).catch(() => null),
      Promise.resolve().then(() => data.sentiment()).catch(() => null),
      Promise.resolve().then(() => data.coinPositions(coin)).catch(() => null),
    ]);
    if (!live) return res.status(502).json({ error: "live market data unavailable" });
    res.json(await data.marketBrief(s, live, senti, wp));
  } catch (e) { res.status(502).json({ error: String(e.message || e) }); }
});

// ---------- Bidang 5: Technical Analysis ----------
app.get("/x402/ta/levels/:symbol", async (req, res) => {
  const s = symOr400(req, res); if (!s) return;
  try { res.json(await ta.levels(s)); }
  catch (e) { res.status(502).json({ error: String(e.message || e) }); }
});
app.get("/x402/ta/regime/:symbol", async (req, res) => {
  const s = symOr400(req, res); if (!s) return;
  try { res.json(await ta.regime(s)); }
  catch (e) { res.status(502).json({ error: String(e.message || e) }); }
});

// ---------- Bidang 6: Web Tools ----------
function toolGate(res, limiter) {
  if (!limiter()) { res.status(429).json({ error: "tool rate limit — retry in a few minutes" }); return false; }
  return true;
}
app.get("/x402/web/screenshot", async (req, res) => {
  if (!toolGate(res, tools.webToolsOk)) return;
  try {
    const png = await tools.screenshot(req.query.url, { width: req.query.width, fullPage: req.query.full === "1" });
    res.type("image/png").send(png);
  } catch (e) { res.status(400).json({ error: String(e.message || e) }); }
});
app.get("/x402/web/audit", async (req, res) => {
  if (!toolGate(res, tools.webToolsOk)) return;
  try { res.json(await tools.webAudit(req.query.url)); }
  catch (e) { res.status(400).json({ error: String(e.message || e) }); }
});
app.get("/x402/web/extract", async (req, res) => {
  if (!toolGate(res, tools.webToolsOk)) return;
  try { res.json(await tools.extractText(req.query.url)); }
  catch (e) { res.status(400).json({ error: String(e.message || e) }); }
});

// ---------- Bidang 7: AI Utility ----------
app.post("/x402/ai/summarize", async (req, res) => {
  if (!aiGate(res)) return;
  try {
    let text = String(req.body.text || "");
    if (!text && req.body.url) text = (await tools.extractText(req.body.url)).text;
    if (!text) return res.status(400).json({ error: "need text or url" });
    const style = ["bullets", "paragraph", "tldr"].includes(req.body.style) ? req.body.style : "paragraph";
    const out = await data.aiUtility(
      `Summarize the user's text faithfully as ${style === "bullets" ? "concise bullet points" : style === "tldr" ? "a 1-2 sentence TL;DR" : "one tight paragraph"}. Keep the original language of the text. No preamble.`,
      text.slice(0, 60000), 700);
    res.json({ style, summary: out });
  } catch (e) { res.status(502).json({ error: String(e.message || e) }); }
});
app.post("/x402/ai/translate", async (req, res) => {
  if (!aiGate(res)) return;
  try {
    const text = String(req.body.text || ""), to = String(req.body.to || "en").slice(0, 16);
    if (!text) return res.status(400).json({ error: "need text" });
    const out = await data.aiUtility(
      `Translate the user's text into "${to}". Preserve meaning, tone, register, and formatting. Output ONLY the translation.`,
      text.slice(0, 40000), 1200);
    res.json({ to, translation: out });
  } catch (e) { res.status(502).json({ error: String(e.message || e) }); }
});
app.post("/x402/ai/extract-json", async (req, res) => {
  if (!aiGate(res)) return;
  try {
    const text = String(req.body.text || "");
    const schema = req.body.schema && typeof req.body.schema === "object" ? req.body.schema : null;
    if (!text || !schema) return res.status(400).json({ error: "need text and schema object" });
    const out = await data.aiUtility(
      `Extract structured data from the user's text into JSON exactly matching this schema (keys → meaning): ${JSON.stringify(schema).slice(0, 2000)}. Output ONLY valid JSON, no markdown fences. Use null for missing fields.`,
      text.slice(0, 40000), 1200);
    let parsed; try { parsed = JSON.parse(out.replace(/^```json?\s*|\s*```$/g, "")); } catch { parsed = null; }
    res.json({ data: parsed, raw: parsed ? undefined : out });
  } catch (e) { res.status(502).json({ error: String(e.message || e) }); }
});

// ---------- Bidang 8: Documents & Media ----------
const PDF_CSS = `<style>
@page{size:A4;margin:22mm 18mm}body{font-family:Helvetica,Arial,sans-serif;color:#16181d;line-height:1.55;font-size:11pt}
h1{font-size:20pt;border-bottom:2px solid #22c97f;padding-bottom:6px}h2{font-size:14pt;margin-top:18px}
code,pre{font-family:Menlo,monospace;font-size:9.5pt;background:#f2f4f7;border-radius:4px;padding:2px 4px}
pre{padding:10px;overflow-x:auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #d7dbe2;padding:6px 8px;font-size:10pt}
th{background:#f2f4f7;text-align:left}blockquote{border-left:3px solid #22c97f;margin:0;padding:4px 12px;color:#4a4f58}
</style>`;
app.post("/x402/doc/pdf", async (req, res) => {
  if (!toolGate(res, tools.webToolsOk)) return;
  try {
    let html = String(req.body.html || "");
    if (!html && req.body.markdown) html = marked.parse(String(req.body.markdown));
    if (!html) return res.status(400).json({ error: "need html or markdown" });
    const title = String(req.body.title || "Document").slice(0, 120);
    const doc = `<!doctype html><html><head><meta charset="utf-8"><title>${title.replace(/</g, "&lt;")}</title>${PDF_CSS}</head><body>${html}</body></html>`;
    const pdf = await tools.htmlToPdf(doc);
    res.type("application/pdf").send(pdf);
  } catch (e) { res.status(400).json({ error: String(e.message || e) }); }
});
app.post("/x402/media/remove-bg", async (req, res) => {
  if (!toolGate(res, tools.mediaOk)) return;
  try {
    let buf = null;
    if (req.body.image_b64) {
      buf = Buffer.from(String(req.body.image_b64).replace(/^data:[^,]*,/, ""), "base64");
    } else if (req.body.url) {
      const u = await tools.ssrfGuard(req.body.url);
      const r = await fetch(u); buf = Buffer.from(await r.arrayBuffer());
    }
    if (!buf || !buf.length) return res.status(400).json({ error: "need image_b64 or url" });
    const png = await tools.removeBg(buf);
    res.type("image/png").send(png);
  } catch (e) { res.status(400).json({ error: String(e.message || e) }); }
});

app.listen(PORT, "127.0.0.1", () => {
  console.log(`Verdix x402 :${PORT} — payTo=${PAY_TO ? PAY_TO.slice(0, 10) + "…" : "(BELUM DISET — route berbayar 503)"} upstream=${UPSTREAM}`);
});
