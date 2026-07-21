// Verdix x402 — endpoint berbayar (USDC di Base) di atas Verdix Reputation API.
// Caller (manusia/agent) bayar per-request via protokol x402; tanpa akun/API key.
// Publik: https://verdix-api.kilatlab.com/x402/...  (nginx → 127.0.0.1:8402)
// PAY_TO wajib diisi (alamat wallet awal) — tanpa itu route berbayar balas 503.

const express = require("express");
const { paymentMiddleware } = require("@x402/express");
const { x402ResourceServer, HTTPFacilitatorClient } = require("@x402/core/server");
const { ExactEvmScheme } = require("@x402/evm/exact/server");
const { declareDiscoveryExtension } = require("@x402/extensions");

const PAY_TO = process.env.X402_PAY_TO || "";
const PORT = parseInt(process.env.X402_PORT || "8402", 10);
const UPSTREAM = process.env.VERDIX_API || "http://127.0.0.1:8600";
// Default Base Sepolia (facilitator publik x402.org). Mainnet (eip155:8453)
// butuh facilitator CDP Coinbase + API key → set X402_NETWORK + X402_FACILITATOR.
const NETWORK = process.env.X402_NETWORK || "eip155:84532";
const FACILITATOR = process.env.X402_FACILITATOR || "https://x402.org/facilitator";

const app = express();
app.disable("x-powered-by");

// ---------- katalog servis (harga & deskripsi satu sumber) ----------
const SERVICES = {
  "GET /x402/agents": {
    price: "$0.002", upstream: () => "/agents", mime: "application/json",
    desc: "All Verdix-native AI agents with live Trust Score, verified on-chain actions, and VDX stake.",
    example: { agents: [{ agentId: 1, trustScore: 57.9, n_subject: 11 }] },
  },
  "GET /x402/agent/:id": {
    price: "$0.005", upstream: (p) => `/agent/${p.id}`, mime: "application/json",
    desc: "Full Trust Score breakdown for one Verdix agent — every formula component, raw, from on-chain economic memory.",
    example: { agentId: 1, trustScore: 57.9, success_rate: 0.884 },
  },
  "GET /x402/agent/:id/cv": {
    price: "$0.005", upstream: (p) => `/agent/${p.id}/cv`, mime: "text/markdown",
    desc: "The agent's Economic CV in markdown — its verifiable track record as a document.",
    example: { markdown: "# Economic CV — Verdix Agent #1 ..." },
  },
  "GET /x402/entries": {
    price: "$0.002", upstream: () => "/entries", mime: "application/json",
    desc: "Latest Economic Memory entries recorded on-chain (BSC testnet), with payload hashes.",
    example: { entries: [{ entryId: 12, outcome: 0 }] },
  },
  "GET /x402/bitagent": {
    price: "$0.005", upstream: () => "/bitagent", mime: "application/json",
    desc: "Trust-score leaderboard of the BitAgent ecosystem (Unibase AIP, 60+ agents), survivorship-aware.",
    example: { agents: [{ handle: "weather", trustScore: 58.9 }] },
  },
  "GET /x402/bitagent/:handle": {
    price: "$0.005", upstream: (p) => `/bitagent/${encodeURIComponent(p.handle)}`, mime: "application/json",
    desc: "Score detail + on-chain ERC-8004 identity check for one BitAgent ecosystem agent.",
    example: { handle: "weather", trustScore: 58.9, identity_verified_onchain: true },
  },
  "GET /x402/memory/:hash": {
    price: "$0.003", upstream: (p) => `/memory/${encodeURIComponent(p.hash)}`, mime: "application/json",
    desc: "The verified payload behind an on-chain Economic Memory dataHash, fetched from Membase.",
    example: { dataHash: "0x...", payload: {} },
  },
  "GET /x402/dossier/:id": {
    price: "$0.02", upstream: null, mime: "application/json", // komposit, dirakit lokal
    desc: "Premium composite dossier for one Verdix agent: profile + score components + full recent memory + Economic CV, in one call.",
    example: { profile: {}, entries: [], cv: "# Economic CV ..." },
  },
};

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
      extensions: { ...declareDiscoveryExtension({ output: { example: s.example } }) },
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
<p class="foot">Verdix — verifiable economic memory for AI agents · data services, not investment advice · <a href="https://verdix.pages.dev/">verdix.pages.dev</a></p>
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

app.listen(PORT, "127.0.0.1", () => {
  console.log(`Verdix x402 :${PORT} — payTo=${PAY_TO ? PAY_TO.slice(0, 10) + "…" : "(BELUM DISET — route berbayar 503)"} upstream=${UPSTREAM}`);
});
