#!/usr/bin/env python3
"""Verdix Reputation API — Layer 4 output, baca langsung dari chain publik.

Endpoint (read-only, cache 60s):
  GET /                → info + daftar endpoint
  GET /agents          → daftar agentId + Trust Score
  GET /agent/<id>      → Trust Score + breakdown komponen (JSON)
  GET /agent/<id>/cv   → Economic CV (markdown)
  GET /memory/<hash>   → payload di balik dataHash on-chain, diambil dari
                         Membase (Unibase DA) + verifikasi hash (moat v9:
                         on-chain = bukti, payload = Membase)
  GET /bitagent            → leaderboard Trust Score agent BitAgent (chain 97)
  GET /bitagent/<handle>   → skor detail + verifikasi identity ERC-8004 on-chain

Semua angka dihitung on-the-fly dari EconomicMemory + controlChangesOf di BSC
testnet — tidak ada database; chain adalah sumber kebenarannya.
"""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import webui  # noqa: E402
from bitagent.indexer import fetch_agents, score_agent  # noqa: E402
from demo.export_entries import SEL_AGENT_COUNT, eth_call, get_entries, get_rotations  # noqa: E402
from intel.trustscore import compute, economic_cv  # noqa: E402

try:  # payload store butuh membase SDK (venv); tanpa itu endpoint /memory nonaktif
    from payloads.membase_store import fetch_payload

    HAS_MEMBASE = True
except Exception:
    HAS_MEMBASE = False

RPC = os.environ.get("VERDIX_RPC", "https://bsc-testnet.bnbchain.org")
MEMORY = os.environ.get("VERDIX_MEMORY", "0x8692F4Bbc7422139D4335AF01734bEbe99516900")
REGISTRY = os.environ.get("VERDIX_REGISTRY", "0x03E3701c98CFe457460BDe6b71d9b466CDC6cBe0")
VDX_STAKING = os.environ.get("VERDIX_STAKING", "0xf3294C1cC9308DD507aeB9E4D4acc9D2b4062ccB")
SEL_STAKED_OF = "0x11f1c8bf"  # stakedOf(uint256)
PORT = int(os.environ.get("VERDIX_API_PORT", "8600"))
CACHE_TTL = 60.0

_cache: dict[str, tuple[float, object]] = {}


def cached(key: str, fn):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    val = fn()
    _cache[key] = (now, val)
    return val


def chain_state():
    def load():
        entries = get_entries(RPC, MEMORY)
        rotations = get_rotations(RPC, REGISTRY)
        n_agents = int(eth_call(RPC, REGISTRY, SEL_AGENT_COUNT), 16)
        return {"entries": entries, "rotations": rotations, "n_agents": n_agents}

    return cached("chain", load)


def vdx_staked(agent_id: int) -> float:
    """Skin in the game (VDX staked utk agent) — ditampilkan apa adanya;
    tidak mengubah formula Trust Score yang sudah dipublikasikan."""
    try:
        raw = eth_call(RPC, VDX_STAKING, SEL_STAKED_OF + format(agent_id, "064x"))
        return int(raw, 16) / 1e18
    except Exception:
        return 0.0


def agent_payload(agent_id: int) -> dict:
    st = chain_state()
    rot = st["rotations"].get(str(agent_id), [])
    c = compute(st["entries"], agent_id, control_changes=rot)
    return {"agentId": agent_id, "trustScore": c.score(),
            "vdxStaked": cached(f"stake:{agent_id}", lambda: vdx_staked(agent_id)),
            **c.__dict__}


class Handler(BaseHTTPRequestHandler):
    server_version = "VerdixAPI/0.1"

    def log_message(self, fmt, *args):  # jangan spam journal
        pass

    def _reply(self, code: int, body: str, ctype: str = "application/json"):
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        try:
            parts = [p for p in self.path.split("?")[0].split("/") if p]
            # alias /api/<x> → /<x>: contoh curl yang diiklankan (verdix.pages.dev/api/...)
            # harus juga jalan kalau di-hit langsung ke domain API
            if len(parts) > 1 and parts[0] == "api":
                parts = parts[1:]
            if not parts:
                landing = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "landing.html")
                if os.path.exists(landing):
                    self._reply(200, open(landing, encoding="utf-8").read(), ctype="text/html")
                    return
                parts = ["api"]  # fallback: tampilkan info JSON
            if parts[0] == "js" and len(parts) == 2 and parts[1].endswith(".js"):
                fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "js",
                                  os.path.basename(parts[1]))
                if os.path.exists(fp):
                    data = open(fp, "rb").read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/javascript")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self._reply(404, json.dumps({"error": "not found"}))
                return
            if parts[0] == "img" and len(parts) == 2 and parts[1].endswith((".webp", ".png")):
                fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img",
                                  os.path.basename(parts[1]))
                if os.path.exists(fp):
                    data = open(fp, "rb").read()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png" if fp.endswith(".png") else "image/webp")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self._reply(404, json.dumps({"error": "not found"}))
                return
            if parts[0] == "fonts" and len(parts) == 2 and parts[1].endswith(".woff2"):
                fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "fonts",
                                  os.path.basename(parts[1]))
                if os.path.exists(fp):
                    data = open(fp, "rb").read()
                    self.send_response(200)
                    self.send_header("Content-Type", "font/woff2")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self._reply(404, json.dumps({"error": "not found"}))
                return
            if parts == ["api"]:
                self._reply(
                    200,
                    json.dumps(
                        {
                            "service": "Verdix Reputation API",
                            "chain": {"rpc": RPC, "memory": MEMORY, "registry": REGISTRY},
                            "endpoints": ["/agents", "/agent/<id>", "/agent/<id>/cv",
                                          "/memory/<dataHash>", "/bitagent", "/bitagent/<handle>"],
                            "membase": HAS_MEMBASE,
                        },
                        indent=2,
                    ),
                )
            elif parts == ["entries"]:
                st = chain_state()
                recent = st["entries"][-20:][::-1]
                self._reply(200, json.dumps({"count": len(st["entries"]), "recent": recent}, indent=2))
            elif parts == ["agents"]:
                st = chain_state()
                names = {1: "smc-bot", 2: "reku"}
                agents = []
                for i in range(1, st["n_agents"] + 1):
                    p = agent_payload(i)
                    agents.append({
                        "agentId": i,
                        "name": names.get(i, f"agent-{i}"),
                        "trustScore": p["trustScore"],
                        "verifiedActions": p["n_subject"],
                        "vdxStaked": p["vdxStaked"],
                        "foundingOperator": i <= 7,
                        "profile": f"https://verdix.pages.dev/web/agent/{i}",
                        "detail": f"https://verdix.pages.dev/api/agent/{i}",
                    })
                self._reply(200, json.dumps({"count": len(agents), "agents": agents}, indent=2))
            elif parts[0] == "web":
                if len(parts) == 2 and parts[1] == "create":
                    from api.create_page import create_page

                    self._reply(200, create_page(webui.page), ctype="text/html")
                    return
                if len(parts) == 2 and parts[1] == "api":
                    self._reply(200, webui.api_docs_page(), ctype="text/html")
                    return
                if len(parts) == 3 and parts[1] == "vault" and parts[2].startswith("0x") and len(parts[2]) == 42:
                    from api.vault_page import vault_page

                    self._reply(200, vault_page(webui.page, parts[2]), ctype="text/html")
                    return
                st = chain_state()
                if len(parts) == 1:
                    v_agents = [agent_payload(i) for i in range(1, st["n_agents"] + 1)]
                    agents = cached("bitagent", lambda: fetch_agents(chain_id=97))
                    scored = sorted((score_agent(a) for a in agents), key=lambda x: -x["trustScore"])
                    self._reply(200, webui.leaderboard_page(v_agents, scored), ctype="text/html")
                elif parts[1] == "agent" and len(parts) == 3 and parts[2].isdigit():
                    aid = int(parts[2])
                    if not (1 <= aid <= st["n_agents"]):
                        self._reply(404, webui.page("404", "<h1>Agent not found</h1>"), ctype="text/html")
                    else:
                        entries = [e for e in st["entries"]
                                   if e["agentId"] == aid or e.get("counterpartyId") == aid]
                        self._reply(200, webui.verdix_agent_page(
                            agent_payload(aid), entries,
                            "https://testnet.bscscan.com", MEMORY), ctype="text/html")
                elif parts[1] == "bitagent" and len(parts) == 3:
                    agents = cached("bitagent", lambda: fetch_agents(chain_id=97))
                    match = [a for a in agents if a.get("handle") == parts[2]]
                    if not match:
                        self._reply(404, webui.page("404", "<h1>Agent not found</h1>"), ctype="text/html")
                    else:
                        b = cached(f"ba:{parts[2]}", lambda: score_agent(match[0], check_onchain=True))
                        self._reply(200, webui.bitagent_page(b), ctype="text/html")
                else:
                    self._reply(404, webui.page("404", "<h1>404</h1>"), ctype="text/html")
            elif parts[0] == "bitagent":
                agents = cached("bitagent", lambda: fetch_agents(chain_id=97))
                if len(parts) == 1:
                    scored = sorted((score_agent(a) for a in agents), key=lambda x: -x["trustScore"])
                    self._reply(200, json.dumps({"count": len(scored), "leaderboard": scored[:25]}, indent=2))
                else:
                    match = [a for a in agents if a.get("handle") == parts[1]]
                    if not match:
                        self._reply(404, json.dumps({"error": "unknown bitagent handle"}))
                    else:
                        self._reply(200, json.dumps(
                            cached(f"ba:{parts[1]}", lambda: score_agent(match[0], check_onchain=True)),
                            indent=2))
            elif parts[0] == "memory" and len(parts) == 2 and parts[1].startswith("0x"):
                if not HAS_MEMBASE:
                    self._reply(503, json.dumps({"error": "membase not configured"}))
                    return
                res = cached(f"mem:{parts[1].lower()}", lambda: fetch_payload(parts[1]))
                self._reply(200 if res.get("verified") else 404, json.dumps(res, indent=2, default=str))
            elif parts[0] == "agent" and len(parts) >= 2 and parts[1].isdigit():
                agent_id = int(parts[1])
                st = chain_state()
                if not (1 <= agent_id <= st["n_agents"]):
                    self._reply(404, json.dumps({"error": "unknown agent"}))
                    return
                if len(parts) == 3 and parts[2] == "cv":
                    rot = st["rotations"].get(str(agent_id), [])
                    cv = economic_cv(
                        st["entries"], agent_id, name=f"Agent #{agent_id}", control_changes=rot
                    )
                    self._reply(200, cv, ctype="text/markdown")
                else:
                    self._reply(200, json.dumps(agent_payload(agent_id), indent=2))
            else:
                self._reply(404, json.dumps({"error": "not found"}))
        except Exception as exc:  # RPC down dsb — jangan matikan server
            self._reply(502, json.dumps({"error": str(exc)}))


if __name__ == "__main__":
    print(f"Verdix Reputation API :{PORT} — rpc={RPC}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
