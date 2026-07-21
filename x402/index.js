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
app.get("/x402/", (req, res) => {
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
