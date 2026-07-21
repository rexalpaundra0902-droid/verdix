// Sumber data servis x402 — SEMUA akses DB riset read-only (mode=readonly).
// Keputusan Reku 2026-07-21: whale bursts dijual DELAY 15 menit (real-time tetap
// internal buat forward-test bot); bidang AI aktif dgn rate-limit biaya.
const Database = require("better-sqlite3");

const HIST = "/root/smc-bot-v19/research/exp/histfeeds.db";
const WHALE = "/root/smc-bot-v19/research/exp/whale.db";
const BURST_DELAY_MS = 15 * 60 * 1000;

function ro(path) { return new Database(path, { readonly: true, fileMustExist: true }); }
let _hist = null, _whale = null;
function hist() { if (!_hist) _hist = ro(HIST); return _hist; }
function whale() { if (!_whale) _whale = ro(WHALE); return _whale; }

const SYM_RE = /^[A-Z0-9]{2,20}$/;
const ADDR_RE = /^0x[0-9a-fA-F]{40}$/;
const clampDays = (q, def, max) => Math.min(Math.max(parseInt(q || def, 10) || def, 1), max);

// ── Market Intelligence ──────────────────────────────────────────────
// Jendela "days" di-anchor ke titik data TERAKHIR per simbol (arsip nge-lag
// beberapa hari via cron harian) — data_through kasih tahu buyer batasnya.
// Catatan unit: funding.ts = milidetik; metrics/basis.ts = detik.
function histWindow(table, cols, symbol, days, msUnit) {
  const h = hist();
  const mx = h.prepare(`select max(ts) m from ${table} where symbol=?`).get(symbol).m;
  if (!mx) return { symbol, days, n: 0, data_through: null, rows: [] };
  const since = mx - days * 86400 * (msUnit ? 1000 : 1);
  const rows = h.prepare(
    `select ${cols} from ${table} where symbol=? and ts>=? order by ts`).all(symbol, since);
  const throughSec = msUnit ? Math.floor(mx / 1000) : mx;
  return { symbol, days, n: rows.length,
           data_through: new Date(throughSec * 1000).toISOString(), rows };
}

function funding(symbol, days) {
  return histWindow("funding", "ts, rate", symbol, days, true);
}

function oiLsr(symbol, days) {
  const out = histWindow("metrics",
    "ts, oi, oi_val, glob_lsr, top_lsr_acct, top_lsr_pos, taker_ratio", symbol, days, false);
  out.granularity = "5m";
  return out;
}

function basis(symbol, days) {
  return histWindow("basis", "ts, premium", symbol, days, false);
}

function cot() {
  const rows = hist().prepare("select * from cot order by date desc limit 104").all();
  return { source: "CFTC Traders in Financial Futures", markets: "BTC, ETH", n: rows.length, rows };
}

function sentiment() {
  const h = hist();
  const fng = h.prepare("select date, value, cls from fng order by date desc limit 30").all();
  const dvol = h.prepare("select currency, ts, close from dvol order by ts desc limit 60").all();
  const cbprem = h.prepare("select date, prem_pct from cbprem order by date desc limit 30").all();
  const stables = h.prepare("select date, total_usd, usdc from stables order by date desc limit 30").all();
  return { fng: { latest: fng[0], history_30d: fng },
           dvol: { latest: dvol.slice(0, 2), history: dvol },
           coinbase_premium: { latest: cbprem[0], history_30d: cbprem },
           stablecoin_supply: { latest: stables[0], history_30d: stables } };
}

async function liveMarket(symbol) {
  const base = "https://fapi.binance.com";
  const j = (u) => fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const [prem, oi, day] = await Promise.all([
    j(`${base}/fapi/v1/premiumIndex?symbol=${symbol}`),
    j(`${base}/fapi/v1/openInterest?symbol=${symbol}`),
    j(`${base}/fapi/v1/ticker/24hr?symbol=${symbol}`),
  ]);
  if (!prem && !oi && !day) throw new Error("symbol unknown or upstream down");
  return { symbol, ts: Date.now(), premium_index: prem, open_interest: oi, stats_24h: day };
}

// ── Whale Intelligence (Hyperliquid) ─────────────────────────────────
function bursts() {
  const cutoff = Date.now() - BURST_DELAY_MS;
  const rows = whale().prepare(
    "select addr, coin, hr, bucket_end_ms, detect_ms, net_usd, sign " +
    "from burst_tickets where detect_ms <= ? order by detect_ms desc limit 50").all(cutoff);
  return { detector: "coordinated OPEN flow >=$250k/1h across tracked whale cohort",
           delay: "15 minutes",
           note: "sign: +1 net long open, -1 net short open", n: rows.length, bursts: rows };
}

function leaderboard() {
  const w = whale();
  const day = w.prepare("select max(day) d from lb_archive").get().d;
  const rows = w.prepare(
    "select rank, addr, acct_value, pnl_day, roi_day, pnl_week, roi_week, pnl_month, roi_month " +
    "from lb_archive where day=? order by rank limit 100").all(day);
  return { day, survivorship_free: true, n: rows.length, rows };
}

function walletInfo(addr) {
  const w = whale();
  const a = addr.toLowerCase();
  const snap = w.prepare("select * from wallets where lower(addr)=? order by ts desc limit 1").get(a);
  const pos = w.prepare(
    "select coin, szi, entry_px, position_value, unrealized_pnl, lev, ts from positions " +
    "where lower(addr)=? order by ts desc limit 40").all(a);
  const fills = w.prepare(
    "select count(*) n, coalesce(sum(closed_pnl),0) pnl, min(ts_ms) first_ms, max(ts_ms) last_ms " +
    "from fills where lower(addr)=?").get(a);
  if (!snap && !pos.length && !fills.n) return null;
  return { addr, snapshot: snap || null, recent_positions: pos, fills_summary: fills };
}

function coinPositions(coin) {
  const w = whale();
  const latest = w.prepare(
    "select addr, szi, entry_px, position_value, unrealized_pnl, lev, max(ts) ts " +
    "from positions where upper(coin)=? group by addr").all(coin);
  let netUsd = 0, nLong = 0, nShort = 0;
  const top = latest
    .map((p) => ({ ...p, side: p.szi > 0 ? "long" : "short" }))
    .sort((x, y) => Math.abs(y.position_value) - Math.abs(x.position_value));
  for (const p of latest) {
    netUsd += (p.szi > 0 ? 1 : -1) * Math.abs(p.position_value || 0);
    if (p.szi > 0) nLong++; else if (p.szi < 0) nShort++;
  }
  return { coin, tracked_wallets_with_position: latest.length, n_long: nLong, n_short: nShort,
           net_exposure_usd: Math.round(netUsd), top_positions: top.slice(0, 15) };
}

// ── AI Analysis (Claude Haiku, rate-limited utk bound biaya) ─────────
const AI_KEY = process.env.ANTHROPIC_API_KEY || "";
let aiCalls = [];
function aiRateOk() { // maks 30 call / 5 menit
  const now = Date.now();
  aiCalls = aiCalls.filter((t) => now - t < 300000);
  if (aiCalls.length >= 30) return false;
  aiCalls.push(now); return true;
}

async function claude(system, user, maxTokens) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": AI_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model: "claude-haiku-4-5-20251001", max_tokens: maxTokens || 900,
      system, messages: [{ role: "user", content: user }] }),
  });
  if (!r.ok) throw new Error(`anthropic ${r.status}`);
  const d = await r.json();
  return d.content.map((c) => c.text || "").join("");
}

async function agentAudit(id, dossierJson) {
  const audit = await claude(
    "You are a rigorous AI-agent trust auditor. You receive a Verdix dossier (on-chain economic memory, trust score components, economic CV). Write a concise structured audit in markdown: ## Summary, ## Strengths (evidence-based), ## Red Flags, ## Verdict (one line, with confidence). Be skeptical; only claim what the data supports. No investment advice.",
    `Dossier for Verdix agent #${id}:\n\n${JSON.stringify(dossierJson).slice(0, 24000)}`,
    900);
  return { agent_id: Number(id), model: "claude-haiku-4.5", audit };
}

async function marketBrief(symbol, live, senti, whalePos) {
  const brief = await claude(
    "You are a quantitative market analyst. Synthesize the provided live futures snapshot, sentiment composite, and whale positioning into a concise markdown brief: ## Snapshot, ## Positioning & Sentiment, ## Whale Flow, ## What Would Change The Picture. Numbers first, no hype, explicitly note data gaps. End with: 'Not investment advice.'",
    `Symbol: ${symbol}\n\nLIVE:\n${JSON.stringify(live).slice(0, 8000)}\n\nSENTIMENT:\n${JSON.stringify(senti).slice(0, 8000)}\n\nWHALE POSITIONING:\n${JSON.stringify(whalePos).slice(0, 6000)}`,
    1100);
  return { symbol, model: "claude-haiku-4.5", generated_at: new Date().toISOString(), brief };
}

async function aiUtility(system, user, maxTokens) {
  return claude(system, user, maxTokens);
}

module.exports = {
  SYM_RE, ADDR_RE, clampDays,
  funding, oiLsr, basis, cot, sentiment, liveMarket,
  bursts, leaderboard, walletInfo, coinPositions,
  aiEnabled: () => Boolean(AI_KEY), aiRateOk, agentAudit, marketBrief, aiUtility,
};
