// Tools servis x402 bidang Web/AI-utility/Documents/Media.
// Semua fetch URL eksternal lewat ssrfGuard (blok IP privat/localhost).
const { spawn } = require("child_process");
const dns = require("dns").promises;
const net = require("net");
const fs = require("fs");
const os = require("os");
const path = require("path");

const PY_PLAYWRIGHT = "/usr/bin/python3"; // playwright terpasang system-wide
const PY_REMBG = "/root/verdix/x402/.pyvenv/bin/python";
const PY_WEASY = "/root/klinik-toko/venv/bin/python";

// ── rate limiter per-bidang (bound CPU/biaya) ────────────────────────
function makeLimiter(max, windowMs) {
  let calls = [];
  return () => {
    const now = Date.now();
    calls = calls.filter((t) => now - t < windowMs);
    if (calls.length >= max) return false;
    calls.push(now); return true;
  };
}
const webToolsOk = makeLimiter(20, 300000);   // 20 / 5 menit
const mediaOk = makeLimiter(10, 300000);      // 10 / 5 menit (CPU berat)

// ── SSRF guard ───────────────────────────────────────────────────────
function ipPrivate(ip) {
  if (net.isIPv6(ip)) {
    const low = ip.toLowerCase();
    return low === "::1" || low.startsWith("fc") || low.startsWith("fd") ||
           low.startsWith("fe80") || low.startsWith("::ffff:127.") || low.includes("::ffff:10.") ||
           low.includes("::ffff:192.168.");
  }
  const p = ip.split(".").map(Number);
  return p[0] === 127 || p[0] === 10 || p[0] === 0 ||
         (p[0] === 172 && p[1] >= 16 && p[1] <= 31) ||
         (p[0] === 192 && p[1] === 168) || (p[0] === 169 && p[1] === 254);
}

async function ssrfGuard(rawUrl) {
  let u;
  try { u = new URL(String(rawUrl)); } catch { throw new Error("bad url"); }
  if (!/^https?:$/.test(u.protocol)) throw new Error("only http/https");
  if (u.username || u.password) throw new Error("credentials in url not allowed");
  let addrs;
  try { addrs = await dns.lookup(u.hostname, { all: true }); }
  catch { throw new Error("dns lookup failed"); }
  if (!addrs.length || addrs.some((a) => ipPrivate(a.address))) throw new Error("host not allowed");
  return u.toString();
}

// ── spawn helper dgn timeout ─────────────────────────────────────────
function run(cmd, args, { input, timeoutMs } = {}) {
  return new Promise((resolve, reject) => {
    const ch = spawn(cmd, args, { stdio: ["pipe", "pipe", "pipe"] });
    const out = [], err = [];
    const killer = setTimeout(() => { ch.kill("SIGKILL"); reject(new Error("tool timeout")); }, timeoutMs || 45000);
    ch.stdout.on("data", (d) => out.push(d));
    ch.stderr.on("data", (d) => err.push(d));
    ch.on("error", (e) => { clearTimeout(killer); reject(e); });
    ch.on("close", (code) => {
      clearTimeout(killer);
      if (code === 0) resolve(Buffer.concat(out));
      else reject(new Error(`tool exit ${code}: ${Buffer.concat(err).toString().slice(-400)}`));
    });
    if (input) ch.stdin.write(input);
    ch.stdin.end();
  });
}

// ── Web Tools ────────────────────────────────────────────────────────
async function screenshot(rawUrl, { width, fullPage } = {}) {
  const url = await ssrfGuard(rawUrl);
  const w = Math.min(Math.max(parseInt(width || 1280, 10) || 1280, 320), 1920);
  const script = `
import sys, json
from playwright.sync_api import sync_playwright
url, w, full = sys.argv[1], int(sys.argv[2]), sys.argv[3] == "1"
with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    pg = b.new_context(viewport={"width": w, "height": 900}).new_page()
    pg.goto(url, wait_until="networkidle", timeout=25000)
    pg.wait_for_timeout(1200)
    png = pg.screenshot(full_page=full)
    b.close()
sys.stdout.buffer.write(png)
`;
  const tmp = path.join(os.tmpdir(), `shot-${Date.now()}.py`);
  fs.writeFileSync(tmp, script);
  try {
    const png = await run(PY_PLAYWRIGHT, [tmp, url, String(w), fullPage ? "1" : "0"], { timeoutMs: 40000 });
    if (png.length > 8 * 1024 * 1024) throw new Error("screenshot too large");
    return png;
  } finally { fs.unlinkSync(tmp); }
}

async function fetchPage(rawUrl, maxBytes) {
  const url = await ssrfGuard(rawUrl);
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 20000);
  try {
    const r = await fetch(url, { signal: ctrl.signal, redirect: "follow",
      headers: { "User-Agent": "verdix-x402-tools/1.0" } });
    const buf = Buffer.from(await r.arrayBuffer());
    if (buf.length > (maxBytes || 3 * 1024 * 1024)) throw new Error("page too large");
    return { status: r.status, headers: Object.fromEntries(r.headers), body: buf };
  } finally { clearTimeout(t); }
}

function stripHtml(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/\s+/g, " ").trim();
}

async function extractText(rawUrl) {
  const { status, body } = await fetchPage(rawUrl);
  const html = body.toString("utf8");
  const title = (html.match(/<title[^>]*>([^<]*)<\/title>/i) || [])[1] || "";
  const text = stripHtml(html).slice(0, 100000);
  return { url: rawUrl, status, title: title.trim(), chars: text.length, text };
}

async function webAudit(rawUrl) {
  const { status, headers, body } = await fetchPage(rawUrl);
  const html = body.toString("utf8");
  const head = html.split(/<\/head>/i)[0] || "";
  const has = (re) => re.test(head);
  const grab = (re) => (head.match(re) || [])[1] || null;
  const checks = {
    status,
    title: grab(/<title[^>]*>([^<]*)<\/title>/i),
    meta_description: has(/name=["']description["']/i),
    canonical: has(/rel=["']canonical["']/i),
    og_title: has(/property=["']og:title["']/i),
    og_image: has(/property=["']og:image["']/i),
    twitter_card: has(/name=["']twitter:card["']/i),
    json_ld: /application\/ld\+json/i.test(html),
    viewport_meta: has(/name=["']viewport["']/i),
    favicon: has(/rel=["'](?:shortcut )?icon["']/i),
    lang_attr: /<html[^>]+lang=/i.test(html),
    h1_count: (html.match(/<h1[\s>]/gi) || []).length,
    img_missing_alt: (html.match(/<img(?![^>]*alt=)[^>]*>/gi) || []).length,
    page_bytes: body.length,
    security_headers: {
      hsts: Boolean(headers["strict-transport-security"]),
      x_frame_options: Boolean(headers["x-frame-options"]),
      csp: Boolean(headers["content-security-policy"]),
      x_content_type_options: Boolean(headers["x-content-type-options"]),
    },
  };
  const issues = [];
  if (!checks.meta_description) issues.push("missing meta description");
  if (!checks.canonical) issues.push("missing canonical");
  if (!checks.og_image) issues.push("missing og:image (no social share card)");
  if (!checks.twitter_card) issues.push("missing twitter:card");
  if (!checks.json_ld) issues.push("no JSON-LD structured data");
  if (checks.h1_count !== 1) issues.push(`h1 count = ${checks.h1_count} (expected 1)`);
  if (checks.img_missing_alt > 0) issues.push(`${checks.img_missing_alt} <img> missing alt`);
  if (!checks.security_headers.hsts) issues.push("no HSTS header");
  if (!checks.security_headers.csp) issues.push("no Content-Security-Policy");
  if (checks.page_bytes > 1500000) issues.push("page over 1.5MB");
  return { url: rawUrl, checks, issues, issue_count: issues.length };
}

// ── Documents (WeasyPrint) ───────────────────────────────────────────
async function htmlToPdf(html) {
  if (Buffer.byteLength(html, "utf8") > 2 * 1024 * 1024) throw new Error("html too large");
  const script = `
import sys
from weasyprint import HTML
sys.stdout.buffer.write(HTML(string=sys.stdin.read()).write_pdf())
`;
  const tmp = path.join(os.tmpdir(), `pdf-${Date.now()}.py`);
  fs.writeFileSync(tmp, script);
  try {
    const pdf = await run(PY_WEASY, [tmp], { input: html, timeoutMs: 40000 });
    if (pdf.length > 15 * 1024 * 1024) throw new Error("pdf too large");
    return pdf;
  } finally { fs.unlinkSync(tmp); }
}

// ── Media (rembg) ────────────────────────────────────────────────────
async function removeBg(imgBuf) {
  if (imgBuf.length > 8 * 1024 * 1024) throw new Error("image too large (max 8MB)");
  const script = `
import sys
from rembg import remove
sys.stdout.buffer.write(remove(sys.stdin.buffer.read()))
`;
  const tmp = path.join(os.tmpdir(), `rembg-${Date.now()}.py`);
  fs.writeFileSync(tmp, script);
  try {
    return await run(PY_REMBG, [tmp], { input: imgBuf, timeoutMs: 90000 });
  } finally { fs.unlinkSync(tmp); }
}

module.exports = { webToolsOk, mediaOk, ssrfGuard, screenshot, extractText, webAudit, htmlToPdf, removeBg };
