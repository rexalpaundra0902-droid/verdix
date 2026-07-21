// Technical Analysis servis — dihitung on-the-fly dari klines publik Binance.
// Self-contained (tanpa import kode bot) — indikator standar: ADX/ATR/EMA/swing.

async function klines(symbol, interval, limit) {
  const r = await fetch(
    `https://fapi.binance.com/fapi/v1/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`);
  if (!r.ok) throw new Error(`klines ${r.status}`);
  const raw = await r.json();
  return raw.map((k) => ({ t: k[0], o: +k[1], h: +k[2], l: +k[3], c: +k[4], v: +k[5] }));
}

const ema = (xs, n) => {
  const k = 2 / (n + 1); let e = xs[0]; const out = [e];
  for (let i = 1; i < xs.length; i++) { e = xs[i] * k + e * (1 - k); out.push(e); }
  return out;
};

function atr(ks, n) {
  const trs = ks.map((k, i) => i === 0 ? k.h - k.l :
    Math.max(k.h - k.l, Math.abs(k.h - ks[i - 1].c), Math.abs(k.l - ks[i - 1].c)));
  return ema(trs, n);
}

function adx(ks, n) {
  const dmP = [], dmM = [], trs = [];
  for (let i = 1; i < ks.length; i++) {
    const up = ks[i].h - ks[i - 1].h, dn = ks[i - 1].l - ks[i].l;
    dmP.push(up > dn && up > 0 ? up : 0);
    dmM.push(dn > up && dn > 0 ? dn : 0);
    trs.push(Math.max(ks[i].h - ks[i].l, Math.abs(ks[i].h - ks[i - 1].c), Math.abs(ks[i].l - ks[i - 1].c)));
  }
  const sm = (xs) => ema(xs, n);
  const trS = sm(trs), pS = sm(dmP), mS = sm(dmM);
  const dxs = trS.map((t, i) => {
    const dip = 100 * pS[i] / (t || 1), dim = 100 * mS[i] / (t || 1);
    return 100 * Math.abs(dip - dim) / ((dip + dim) || 1);
  });
  const adxs = ema(dxs, n);
  const last = adxs.length - 1;
  return { adx: adxs[last], di_plus: 100 * pS[last] / (trS[last] || 1), di_minus: 100 * mS[last] / (trS[last] || 1) };
}

function swings(ks, look) {
  const highs = [], lows = [];
  for (let i = look; i < ks.length - look; i++) {
    const w = ks.slice(i - look, i + look + 1);
    if (ks[i].h === Math.max(...w.map((x) => x.h))) highs.push({ t: ks[i].t, px: ks[i].h });
    if (ks[i].l === Math.min(...w.map((x) => x.l))) lows.push({ t: ks[i].t, px: ks[i].l });
  }
  return { highs: highs.slice(-8), lows: lows.slice(-8) };
}

async function levels(symbol) {
  const [h4, d1] = await Promise.all([klines(symbol, "4h", 400), klines(symbol, "1d", 200)]);
  const price = h4[h4.length - 1].c;
  const s4 = swings(h4, 2), sd = swings(d1, 2);
  const near = (arr) => arr
    .map((x) => ({ ...x, dist_pct: +(100 * (x.px - price) / price).toFixed(2) }))
    .sort((a, b) => Math.abs(a.dist_pct) - Math.abs(b.dist_pct)).slice(0, 5);
  return {
    symbol, price, ts: Date.now(),
    swing_4h: { resistance: near(s4.highs.filter((x) => x.px > price)),
                support: near(s4.lows.filter((x) => x.px < price)) },
    swing_1d: { resistance: near(sd.highs.filter((x) => x.px > price)),
                support: near(sd.lows.filter((x) => x.px < price)) },
    note: "swing fractal 2-bar; dist_pct relative to last price",
  };
}

async function regime(symbol) {
  const h4 = await klines(symbol, "4h", 500);
  const closes = h4.map((k) => k.c);
  const price = closes[closes.length - 1];
  const a = adx(h4, 14);
  const atrs = atr(h4, 14);
  const atrPct = 100 * atrs[atrs.length - 1] / price;
  const atrHist = atrs.map((x, i) => 100 * x / closes[i]).slice(-300).sort((x, y) => x - y);
  const volPctile = Math.round(100 * atrHist.findIndex((x) => x >= atrPct) / atrHist.length);
  const e50 = ema(closes, 50).pop(), e200 = ema(closes, 200).pop();
  const trend = a.adx >= 25 ? (a.di_plus > a.di_minus ? "trending_up" : "trending_down")
    : a.adx >= 18 ? "weak_trend" : "ranging";
  return {
    symbol, price, ts: Date.now(), timeframe: "4h",
    adx14: +a.adx.toFixed(1), di_plus: +a.di_plus.toFixed(1), di_minus: +a.di_minus.toFixed(1),
    atr14_pct: +atrPct.toFixed(3), atr_percentile_300bar: volPctile >= 0 ? volPctile : 100,
    ema50: +e50.toFixed(2), ema200: +e200.toFixed(2),
    ema_bias: price > e50 && e50 > e200 ? "bullish" : price < e50 && e50 < e200 ? "bearish" : "mixed",
    regime: trend,
    note: "standard indicators, standard params; not investment advice",
  };
}

module.exports = { levels, regime };
