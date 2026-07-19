#!/usr/bin/env python3
"""Verdix Trust Directory — halaman web publik (server-side render, tanpa dependency).

Dipakai api/server.py:
  GET /web                → leaderboard: agent Verdix + seluruh agent BitAgent chain 97
  GET /web/agent/<id>     → profil agent Verdix (on-chain economic memory)
  GET /web/bitagent/<h>   → profil agent BitAgent (platform stats + cek identity on-chain)
"""

from __future__ import annotations

import html

CSS = """
:root{color-scheme:dark}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#07090f;color:#e8ecf4;font:15px/1.65 system-ui,-apple-system,sans-serif;padding:28px 20px;max-width:1000px;margin:0 auto;position:relative}
body::before{content:'';position:fixed;inset:0;z-index:-1;background:
 radial-gradient(600px 400px at 85% -10%,rgba(139,92,246,.16),transparent 60%),
 radial-gradient(700px 500px at -10% 20%,rgba(52,211,153,.10),transparent 60%),
 linear-gradient(rgba(122,162,255,.035) 1px,transparent 1px),
 linear-gradient(90deg,rgba(122,162,255,.035) 1px,transparent 1px);
 background-size:auto,auto,44px 44px,44px 44px}
a{color:#7aa2ff;text-decoration:none;transition:.2s}a:hover{color:#a5c0ff}
h1{font-size:clamp(24px,4vw,32px);font-weight:800;margin-bottom:4px;
 background:linear-gradient(90deg,#e8ecf4,#34d399 55%,#7aa2ff);-webkit-background-clip:text;background-clip:text;color:transparent}
h2{font-size:18px;margin:26px 0 10px;color:#cdd6e4}
.sub{color:#8b93a7;margin-bottom:20px}
.badge{display:inline-block;padding:3px 12px;border-radius:99px;font-size:12px;font-weight:700;letter-spacing:.02em}
.b-ok{background:rgba(52,211,153,.12);color:#34d399;border:1px solid rgba(52,211,153,.35)}
.b-warn{background:rgba(251,191,36,.1);color:#fbbf24;border:1px solid rgba(251,191,36,.3)}
.b-dim{background:#161b28;color:#8b93a7;border:1px solid #202839}
table{width:100%;border-collapse:collapse;margin-top:8px}
th{color:#8b93a7;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.08em;padding:9px 12px;border-bottom:1px solid #1b2232}
td{padding:11px 12px;border-bottom:1px solid #121826}
tr{transition:.15s}tr:hover td{background:rgba(122,162,255,.05)}
.score{font-weight:800;font-variant-numeric:tabular-nums}
.big{font-size:clamp(36px,6vw,52px);font-weight:900;line-height:1.05;
 background:linear-gradient(120deg,#34d399,#7aa2ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.card{background:rgba(16,21,33,.72);border:1px solid #1b2232;border-radius:16px;padding:20px;margin:14px 0;
 backdrop-filter:blur(8px);box-shadow:0 0 0 1px rgba(122,162,255,.03),0 8px 32px rgba(0,0,0,.35);transition:.25s}
.card:hover{border-color:rgba(52,211,153,.35);box-shadow:0 0 24px rgba(52,211,153,.07),0 8px 32px rgba(0,0,0,.35)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.kv .k{color:#8b93a7;font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.kv .v{font-size:17px;font-weight:700;margin-top:2px;word-break:break-all}
.bar{height:8px;background:#161b28;border-radius:99px;overflow:hidden;margin-top:5px}
.bar>div{height:100%;background:linear-gradient(90deg,#34d399,#7aa2ff);box-shadow:0 0 10px rgba(52,211,153,.5)}
.mono{font-family:ui-monospace,SFMono-Regular,monospace;font-size:13px}
.foot{color:#5b6172;font-size:12px;margin-top:30px;border-top:1px solid #121826;padding-top:14px}
.tblwrap{overflow-x:auto}
button{background:linear-gradient(90deg,#34d399,#4f8df9);color:#06121c;font-weight:800;border:0;border-radius:10px;
 padding:10px 18px;cursor:pointer;transition:.2s;box-shadow:0 0 18px rgba(52,211,153,.25)}
button:hover{transform:translateY(-1px);box-shadow:0 0 26px rgba(52,211,153,.45)}
input{width:100%;padding:9px 10px;background:#0a0e18;border:1px solid #1b2232;border-radius:9px;color:#e8ecf4;transition:.2s}
input:focus{outline:none;border-color:#34d399;box-shadow:0 0 0 3px rgba(52,211,153,.12)}
"""


NAV = ("<nav style='display:flex;gap:18px;align-items:center;margin-bottom:26px;font-weight:600'>"
       "<a href='/' style='font-weight:900;font-size:17px;letter-spacing:.02em'>"
       "<span style='color:#34d399'>◆</span> VERDIX</a>"
       "<span style='flex:1'></span>"
       "<a href='/web'>Directory</a><a href='/web/create'>Launch App</a>"
       "<a href='https://github.com/rexalpaundra0902-droid/verdix'>GitHub</a></nav>")


def page(title: str, body: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body>{NAV}{body}<p class='foot'>Verdix — verifiable economic memory for AI agents · "
            f"live data from BSC testnet &amp; Membase · "
            f"<a href='https://github.com/rexalpaundra0902-droid/verdix'>source</a> · testnet only, not investment advice</p></body></html>")


def score_badge(s: float) -> str:
    cls = "b-ok" if s >= 55 else ("b-warn" if s >= 30 else "b-dim")
    return f"<span class='badge {cls}'>{s:.1f}</span>"


def leaderboard_page(verdix_agents: list[dict], bitagents: list[dict]) -> str:
    vrows = "".join(
        f"<tr><td><a href='/web/agent/{a['agentId']}'>Agent #{a['agentId']}</a>"
        f"{' · smc-bot' if a['agentId'] == 1 else ''}</td>"
        f"<td class='score'>{score_badge(a['trustScore'])}</td>"
        f"<td>{a.get('n_subject', 0)} verified actions</td>"
        f"<td>{a.get('vdxStaked', 0):,.0f} VDX staked</td></tr>"
        for a in verdix_agents)
    brows = "".join(
        f"<tr><td><a href='/web/bitagent/{html.escape(str(b['handle']))}'>{html.escape(str(b['name'] or b['handle']))}</a></td>"
        f"<td class='score'>{score_badge(b['trustScore'])}</td>"
        f"<td>{int(b['raw_stats']['completed_jobs'])}/{int(b['raw_stats']['total_jobs'])} jobs</td>"
        f"<td>${b['raw_stats']['total_revenue_usd']:.4f}</td>"
        f"<td>{'🟢' if b.get('online') else '⚪'}</td></tr>"
        for b in bitagents)
    body = (
        "<h1>Verdix Trust Directory</h1>"
        "<p class='sub'>Skor kepercayaan AI agent — dihitung dari bukti, bukan klaim. "
        "Economic memory on-chain (BSC testnet) + payload terverifikasi di Membase. "
        "<a href='/web/create'><b>→ Create your Verified Agent Vault</b></a></p>"
        "<h2>Verdix-native agents (full on-chain economic memory)</h2>"
        "<div class='tblwrap'><table><tr><th>Agent</th><th>Trust Score</th><th>History</th><th>Skin in the game</th></tr>"
        f"{vrows}</table></div>"
        f"<h2>BitAgent ecosystem (Unibase AIP, chain 97) — {len(bitagents)} agents</h2>"
        "<div class='tblwrap'><table><tr><th>Agent</th><th>Trust Score</th><th>Jobs</th><th>Revenue</th><th></th></tr>"
        f"{brows}</table></div>")
    return page("Verdix Trust Directory", body)


def _component_bars(components: dict[str, float]) -> str:
    out = ""
    for k, v in components.items():
        pct = max(0.0, min(1.0, float(v))) * 100
        out += (f"<div class='kv'><div class='k'>{html.escape(k)}</div>"
                f"<div class='v'>{float(v):.3f}</div><div class='bar'><div style='width:{pct:.0f}%'></div></div></div>")
    return out


def verdix_agent_page(p: dict, entries: list[dict], explorer: str, memory_addr: str) -> str:
    comp = {
        "success rate": p["success_rate"], "economic volume": p["economic_volume"],
        "counterparty diversity": p["counterparty_diversity"], "stress behavior": p["stress_behavior"],
        "dispute record": p["dispute_component"],
    }
    ent_rows = "".join(
        f"<tr><td class='mono'>#{e['entryId']}</td><td>C{e['actionClass']}/T{e['tier']}</td>"
        f"<td>{['✅ success','❌ failed','⚖️ for','⚖️ against'][e['outcome']]}</td>"
        f"<td class='mono'><a href='/memory/{e['dataHash']}'>{e['dataHash'][:18]}…</a></td></tr>"
        for e in entries[-15:][::-1])
    body = (
        f"<p><a href='/web'>← directory</a></p>"
        f"<h1>Verdix Agent #{p['agentId']}{' · smc-bot' if p['agentId'] == 1 else ''}</h1>"
        f"<p class='sub'>Identity ERC-8004 · economic memory on-chain · payload di Membase</p>"
        f"<div class='card'><div class='grid'>"
        f"<div class='kv'><div class='k'>Trust Score</div><div class='big'>{p['trustScore']:.1f}</div></div>"
        f"<div class='kv'><div class='k'>Verified actions</div><div class='v'>{p['n_subject']}</div></div>"
        f"<div class='kv'><div class='k'>VDX staked</div><div class='v'>{p.get('vdxStaked', 0):,.0f}</div></div>"
        f"<div class='kv'><div class='k'>Kalah dispute</div><div class='v'>{p['disputes_against']}</div></div>"
        f"<div class='kv'><div class='k'>Perpindahan kontrol</div><div class='v'>{p['n_control_changes']}</div></div>"
        f"</div></div>"
        f"<h2>Komponen skor</h2><div class='card'><div class='grid'>{_component_bars(comp)}</div></div>"
        f"<h2>Economic memory (15 terakhir)</h2>"
        f"<div class='tblwrap'><table><tr><th>Entry</th><th>Class/Tier</th><th>Outcome</th><th>Payload (verifikasi)</th></tr>{ent_rows}</table></div>"
        f"<p class='sub' style='margin-top:12px'>Verifikasi mandiri: "
        f"<a href='{explorer}/address/{memory_addr}#readContract'>EconomicMemory di BscScan</a> · "
        f"<a href='/agent/{p['agentId']}'>raw JSON</a> · <a href='/agent/{p['agentId']}/cv'>Economic CV</a></p>")
    return page(f"Verdix Agent #{p['agentId']}", body)


def bitagent_page(b: dict) -> str:
    comp = b["components"]
    onchain = b.get("identity_verified_onchain")
    ver = ("<span class='badge b-ok'>identity verified on-chain ✓</span>" if onchain
           else "<span class='badge b-warn'>identity belum terverifikasi on-chain</span>")
    body = (
        f"<p><a href='/web'>← directory</a></p>"
        f"<h1>{html.escape(str(b['name'] or b['handle']))}</h1>"
        f"<p class='sub mono'>{html.escape(str(b['agent_id']))}</p>"
        f"<div class='card'><div class='grid'>"
        f"<div class='kv'><div class='k'>Trust Score</div><div class='big'>{b['trustScore']:.1f}</div></div>"
        f"<div class='kv'><div class='k'>Jobs</div><div class='v'>{int(b['raw_stats']['completed_jobs'])}/{int(b['raw_stats']['total_jobs'])}</div></div>"
        f"<div class='kv'><div class='k'>Revenue</div><div class='v'>${b['raw_stats']['total_revenue_usd']:.4f}</div></div>"
        f"<div class='kv'><div class='k'>Status</div><div class='v'>{'online' if b.get('online') else 'offline'}</div></div>"
        f"</div><p style='margin-top:10px'>{ver}</p></div>"
        f"<h2>Komponen skor</h2><div class='card'><div class='grid'>{_component_bars(comp)}</div></div>"
        f"<p class='sub'>Sumber: {html.escape(b['source'])} · <a href='/bitagent/{html.escape(str(b['handle']))}'>raw JSON</a></p>")
    return page(f"{b['handle']} — Verdix Trust", body)
