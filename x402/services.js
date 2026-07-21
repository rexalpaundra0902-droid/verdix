// Katalog servis x402 Verdix — 4 bidang, satu sumber untuk harga/deskripsi/route.
// Handler data ada di data.js; index.js merakit middleware + express route.

const SERVICES = {
  // ── Bidang 1: Agent Trust (Verdix core) ─────────────────────────────
  "GET /x402/agents": {
    group: "Agent Trust", price: "$0.002", mime: "application/json",
    desc: "All Verdix-native AI agents with live Trust Score, verified on-chain actions, and VDX stake.",
    example: { agents: [{ agentId: 1, trustScore: 57.9, n_subject: 11 }] },
  },
  "GET /x402/agent/:id": {
    group: "Agent Trust", price: "$0.005", mime: "application/json",
    desc: "Full Trust Score breakdown for one Verdix agent — every formula component, raw, from on-chain economic memory.",
    example: { agentId: 1, trustScore: 57.9, success_rate: 0.884 },
  },
  "GET /x402/agent/:id/cv": {
    group: "Agent Trust", price: "$0.005", mime: "text/markdown",
    desc: "The agent's Economic CV in markdown — its verifiable track record as a document.",
    example: { markdown: "# Economic CV — Verdix Agent #1 ..." },
  },
  "GET /x402/entries": {
    group: "Agent Trust", price: "$0.002", mime: "application/json",
    desc: "Latest Economic Memory entries recorded on-chain, with payload hashes.",
    example: { entries: [{ entryId: 12, outcome: 0 }] },
  },
  "GET /x402/bitagent": {
    group: "Agent Trust", price: "$0.005", mime: "application/json",
    desc: "Trust-score leaderboard of the BitAgent ecosystem (Unibase AIP, 60+ agents).",
    example: { agents: [{ handle: "weather", trustScore: 58.9 }] },
  },
  "GET /x402/bitagent/:handle": {
    group: "Agent Trust", price: "$0.005", mime: "application/json",
    desc: "Score detail + on-chain ERC-8004 identity check for one BitAgent ecosystem agent.",
    example: { handle: "weather", trustScore: 58.9, identity_verified_onchain: true },
  },
  "GET /x402/memory/:hash": {
    group: "Agent Trust", price: "$0.003", mime: "application/json",
    desc: "The verified payload behind an on-chain Economic Memory dataHash, fetched from Membase.",
    example: { dataHash: "0x...", payload: {} },
  },
  "GET /x402/dossier/:id": {
    group: "Agent Trust", price: "$0.02", mime: "application/json",
    desc: "Premium composite dossier for one Verdix agent: profile + score components + recent memory + Economic CV in one call.",
    example: { profile: {}, recent_entries: [], economic_cv: "# ..." },
  },

  // ── Bidang 2: Market Intelligence (arsip 2021→now + live) ───────────
  "GET /x402/market/funding/:symbol": {
    group: "Market Intelligence", price: "$0.005", mime: "application/json",
    desc: "Historical perp funding rates for a symbol (Binance, 8h) — archive back to 2021. Query: ?days=30 (max 365).",
    example: { symbol: "BTCUSDT", rows: [{ ts: 1700000000, rate: 0.0001 }] },
  },
  "GET /x402/market/oi-lsr/:symbol": {
    group: "Market Intelligence", price: "$0.01", mime: "application/json",
    desc: "Open-interest + long/short-ratio history (5m granularity, archive since 2021 — deleted from public APIs after 30 days). Query: ?days=7 (max 90).",
    example: { symbol: "BTCUSDT", rows: [{ ts: 1700000000, oi: 84000, glob_lsr: 1.9 }] },
  },
  "GET /x402/market/basis/:symbol": {
    group: "Market Intelligence", price: "$0.005", mime: "application/json",
    desc: "Perp premium/basis history for a symbol. Query: ?days=30 (max 365).",
    example: { symbol: "BTCUSDT", rows: [{ ts: 1700000000, premium: 0.0002 }] },
  },
  "GET /x402/market/cot": {
    group: "Market Intelligence", price: "$0.01", mime: "application/json",
    desc: "CFTC Traders-in-Financial-Futures positioning for BTC & ETH futures — dealer/asset-manager/leveraged-fund longs & shorts, weekly.",
    example: { rows: [{ date: "2026-07-14", market: "BTC", lev_long: 12000 }] },
  },
  "GET /x402/market/sentiment": {
    group: "Market Intelligence", price: "$0.01", mime: "application/json",
    desc: "Composite sentiment snapshot: Fear&Greed, Deribit DVOL, Coinbase premium, stablecoin supply — latest + 30d context.",
    example: { fng: { value: 54 }, dvol: {}, cbprem: {}, stables: {} },
  },
  "GET /x402/market/live/:symbol": {
    group: "Market Intelligence", price: "$0.003", mime: "application/json",
    desc: "Live snapshot for a symbol: mark price, current funding, open interest, 24h stats (Binance futures).",
    example: { symbol: "BTCUSDT", markPrice: 120000, fundingRate: 0.0001 },
  },

  // ── Bidang 3: Whale Intelligence (Hyperliquid) ──────────────────────
  "GET /x402/whale/bursts": {
    group: "Whale Intelligence", price: "$0.05", mime: "application/json",
    desc: "PREMIUM — whale burst events (15-min delayed): coordinated OPEN flow ≥$250k/1h across tracked Hyperliquid whale wallets, with direction sign. Same detector as our internal research; real-time tier on request.",
    example: { bursts: [{ coin: "BTC", net_usd: 310000, sign: 1 }] },
  },
  "GET /x402/whale/leaderboard": {
    group: "Whale Intelligence", price: "$0.01", mime: "application/json",
    desc: "Survivorship-free Hyperliquid whale leaderboard archive — daily snapshots incl. wallets that later blew up.",
    example: { day: "2026-07-20", rows: [{ addr: "0x...", roi_month: 0.4 }] },
  },
  "GET /x402/whale/wallet/:addr": {
    group: "Whale Intelligence", price: "$0.02", mime: "application/json",
    desc: "One Hyperliquid whale wallet: latest snapshot, open positions, recent fills summary (from a 340k-fill archive).",
    example: { addr: "0x...", positions: [], fills_30d: { n: 120, pnl: 5400 } },
  },
  "GET /x402/whale/positions/:coin": {
    group: "Whale Intelligence", price: "$0.02", mime: "application/json",
    desc: "Aggregate whale positioning for one coin: net long/short exposure, wallet count, largest positions (tracked cohort).",
    example: { coin: "BTC", net_usd: 12000000, n_long: 34, n_short: 21 },
  },

  // ── Bidang 4: AI Analysis (Claude) ──────────────────────────────────
  "GET /x402/ai/agent-audit/:id": {
    group: "AI Analysis", price: "$0.05", mime: "application/json",
    desc: "PREMIUM — Claude reads the full Verdix dossier of an agent and writes a structured trust audit: strengths, red flags, verdict.",
    example: { agent_id: 1, audit: "## Trust Audit ..." },
  },
  "GET /x402/ai/market-brief/:symbol": {
    group: "AI Analysis", price: "$0.10", mime: "application/json",
    desc: "FLAGSHIP — Claude synthesizes live price/funding/OI, sentiment composite, and whale positioning into one market brief for a symbol.",
    example: { symbol: "BTCUSDT", brief: "## Market Brief ..." },
  },
};

module.exports = { SERVICES };
