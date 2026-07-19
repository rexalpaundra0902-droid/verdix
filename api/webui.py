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
body{background:#0b0e14;color:#e6e9ef;font:15px/1.6 system-ui,-apple-system,sans-serif;padding:24px;max-width:960px;margin:0 auto}
a{color:#7aa2ff;text-decoration:none}a:hover{text-decoration:underline}
h1{font-size:26px;margin-bottom:4px}h2{font-size:18px;margin:24px 0 10px}
.sub{color:#8b93a7;margin-bottom:20px}
.badge{display:inline-block;padding:2px 10px;border-radius:99px;font-size:12px;font-weight:600}
.b-ok{background:#123524;color:#4ade80}.b-warn{background:#3a2a12;color:#fbbf24}.b-dim{background:#1c2230;color:#8b93a7}
table{width:100%;border-collapse:collapse;margin-top:8px}
th{color:#8b93a7;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;padding:8px 10px;border-bottom:1px solid #1c2230}
td{padding:9px 10px;border-bottom:1px solid #141926}
tr:hover td{background:#10141f}
.score{font-weight:700;font-variant-numeric:tabular-nums}
.big{font-size:44px;font-weight:800;line-height:1.1}
.card{background:#10141f;border:1px solid #1c2230;border-radius:12px;padding:18px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.kv .k{color:#8b93a7;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
.kv .v{font-size:17px;font-weight:600;margin-top:2px;word-break:break-all}
.bar{height:8px;background:#1c2230;border-radius:99px;overflow:hidden;margin-top:4px}
.bar>div{height:100%;background:linear-gradient(90deg,#4ade80,#7aa2ff)}
.mono{font-family:ui-monospace,monospace;font-size:13px}
.foot{color:#5b6172;font-size:12px;margin-top:28px}
.tblwrap{overflow-x:auto}
"""


def page(title: str, body: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body>{body}<p class='foot'>Verdix — verifiable economic memory for AI agents · "
            f"data dihitung live dari BSC testnet &amp; Membase · "
            f"<a href='https://github.com/rexalpaundra0902-droid/verdix'>source</a></p></body></html>")


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
        "Economic memory on-chain (BSC testnet) + payload terverifikasi di Membase.</p>"
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
