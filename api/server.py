#!/usr/bin/env python3
"""Verdix Reputation API — Layer 4 output, baca langsung dari chain publik.

Endpoint (read-only, stdlib only, cache 60s):
  GET /                → info + daftar endpoint
  GET /agents          → daftar agentId + Trust Score
  GET /agent/<id>      → Trust Score + breakdown komponen (JSON)
  GET /agent/<id>/cv   → Economic CV (markdown)

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

from demo.export_entries import SEL_AGENT_COUNT, eth_call, get_entries, get_rotations  # noqa: E402
from intel.trustscore import compute, economic_cv  # noqa: E402

RPC = os.environ.get("VERDIX_RPC", "https://bsc-testnet.bnbchain.org")
MEMORY = os.environ.get("VERDIX_MEMORY", "0x8692F4Bbc7422139D4335AF01734bEbe99516900")
REGISTRY = os.environ.get("VERDIX_REGISTRY", "0x03E3701c98CFe457460BDe6b71d9b466CDC6cBe0")
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


def agent_payload(agent_id: int) -> dict:
    st = chain_state()
    rot = st["rotations"].get(str(agent_id), [])
    c = compute(st["entries"], agent_id, control_changes=rot)
    return {"agentId": agent_id, "trustScore": c.score(), **c.__dict__}


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
            if not parts:
                self._reply(
                    200,
                    json.dumps(
                        {
                            "service": "Verdix Reputation API",
                            "chain": {"rpc": RPC, "memory": MEMORY, "registry": REGISTRY},
                            "endpoints": ["/agents", "/agent/<id>", "/agent/<id>/cv"],
                        },
                        indent=2,
                    ),
                )
            elif parts == ["agents"]:
                st = chain_state()
                agents = [
                    {"agentId": i, "trustScore": agent_payload(i)["trustScore"]}
                    for i in range(1, st["n_agents"] + 1)
                ]
                self._reply(200, json.dumps({"count": len(agents), "agents": agents}, indent=2))
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
