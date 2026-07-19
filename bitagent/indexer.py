#!/usr/bin/env python3
"""Verdix Trust Intelligence untuk agent BitAgent (Unibase AIP).

Sumber data:
  1. AIP platform API (stats job per agent — refleksi settlement ERC-8183)
  2. On-chain verification: identity ERC-8004 agent dicek langsung ke
     AIP Registry (ownerOf tokenId) via eth_call — bukti identity-nya nyata.

Catatan jujur (didokumentasikan, bukan disembunyikan): indexing raw event
ERC-8183 dari chain belum bisa dilakukan karena SEMUA RPC publik BSC testnet
menolak/membatasi eth_getLogs (limit exceeded / 403) dan Etherscan V2 free
tier tidak meng-cover logs chain 97. Begitu ada RPC berbayar, komponen
`platform_stats` di skor ini tinggal diganti feed on-chain murni — bentuk
fungsinya sudah sama.
"""

from __future__ import annotations

import json
import math
import urllib.request

AIP_API = "https://api.aip.unibase.com"
RPC = "https://bsc-testnet.bnbchain.org"
AIP_REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"
SEL_OWNER_OF = "0x6352211e"  # ownerOf(uint256)

W_SUCCESS = 0.45
W_VOLUME = 0.20
W_ACTIVITY = 0.20
W_IDENTITY = 0.15
VOLUME_SATURATION_USD = 1000.0
ACTIVITY_SATURATION_JOBS = 500.0


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "verdix-indexer/0.1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_agents(chain_id: int = 97, limit_pages: int = 10) -> list[dict]:
    """Pagination platform = param `page` (pageSize fix 100); filter chain wajib
    `chain_id` (param lain diabaikan dan malah balikin chain default)."""
    out, seen = [], set()
    for page in range(1, limit_pages + 1):
        d = _get(f"{AIP_API}/agents?chain_id={chain_id}&page={page}")
        rows = d.get("data", [])
        for a in rows:
            key = a.get("agent_id") or a.get("handle")
            if key not in seen:
                seen.add(key)
                out.append(a)
        if len(rows) < 100:
            break
    return out


def verify_identity_onchain(agent_id: str) -> bool | None:
    """agent_id format '97:0xregistry:tokenId' → cek ownerOf di registry."""
    try:
        chain, registry, token_id = agent_id.split(":")
        if chain != "97":
            return None
        data = SEL_OWNER_OF + format(int(token_id), "064x")
        req = urllib.request.Request(
            RPC,
            data=json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                 "params": [{"to": registry, "data": data}, "latest"]}
            ).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "verdix-indexer/0.1"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.load(r)
        owner = res.get("result", "0x0")
        return int(owner, 16) != 0
    except Exception:
        return None


def score_agent(agent: dict, check_onchain: bool = False) -> dict:
    stats = agent.get("stats") or {}
    total = float(stats.get("total_jobs") or 0)
    completed = float(stats.get("completed_jobs") or 0)
    revenue = float(stats.get("total_revenue") or 0)

    success = (completed / total) if total > 0 else 0.0
    volume = min(1.0, math.log10(1 + revenue) / math.log10(1 + VOLUME_SATURATION_USD))
    activity = min(1.0, math.log10(1 + total) / math.log10(1 + ACTIVITY_SATURATION_JOBS))

    identity_verified = None
    if check_onchain:
        identity_verified = verify_identity_onchain(agent.get("agent_id", ""))
    identity = 1.0 if identity_verified else (0.5 if identity_verified is None and agent.get("registered_onchain") else 0.0)

    score = round(100 * (W_SUCCESS * success + W_VOLUME * volume + W_ACTIVITY * activity + W_IDENTITY * identity), 1)
    return {
        "handle": agent.get("handle"),
        "agent_id": agent.get("agent_id"),
        "name": agent.get("display_name"),
        "trustScore": score,
        "components": {
            "success_rate": round(success, 4),
            "economic_volume": round(volume, 4),
            "activity": round(activity, 4),
            "identity": identity,
        },
        "raw_stats": {"total_jobs": total, "completed_jobs": completed, "total_revenue_usd": revenue},
        "identity_verified_onchain": identity_verified,
        "online": agent.get("online"),
        "source": "aip-platform-stats + erc8004-onchain-check",
    }


def leaderboard(agents: list[dict] | None = None, top: int = 20) -> list[dict]:
    agents = agents if agents is not None else fetch_agents()
    scored = [score_agent(a) for a in agents]
    scored.sort(key=lambda x: -x["trustScore"])
    return scored[:top]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        agents = fetch_agents()
        match = [a for a in agents if a.get("handle") == sys.argv[1]]
        print(json.dumps(score_agent(match[0], check_onchain=True) if match else {"error": "not found"}, indent=2))
    else:
        print(json.dumps(leaderboard(top=10), indent=2))
