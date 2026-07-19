#!/usr/bin/env python3
"""Export Economic Memory dari chain → entries.json untuk Trust Intelligence.

Pakai JSON-RPC polos (eth_call) tanpa dependency web3 — Entry adalah struct
statis sehingga decode-nya deterministic per-word.
"""

from __future__ import annotations

import argparse
import json
import urllib.request

SEL_ENTRY_COUNT = "0x0cbb0f83"  # entryCount()
SEL_GET_ENTRY = "0x2cb01ddb"  # getEntry(uint64)


def eth_call(rpc: str, to: str, data: str) -> str:
    req = urllib.request.Request(
        rpc,
        data=json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_call",
                "params": [{"to": to, "data": data}, "latest"],
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(resp["error"])
    return resp["result"]


def word(hexdata: str, i: int) -> int:
    body = hexdata[2:]
    return int(body[i * 64 : (i + 1) * 64], 16)


def word_hex(hexdata: str, i: int) -> str:
    return "0x" + hexdata[2:][i * 64 : (i + 1) * 64]


def get_entries(rpc: str, memory_addr: str) -> list[dict]:
    n = int(eth_call(rpc, memory_addr, SEL_ENTRY_COUNT), 16)
    entries = []
    for i in range(n):
        data = SEL_GET_ENTRY + format(i, "064x")
        out = eth_call(rpc, memory_addr, data)
        # Entry: entryId, agentId, counterpartyId, actionClass, tier,
        #        valueWei, outcome, dataHash, timestamp, recorder — 10 static words
        entries.append(
            {
                "entryId": word(out, 0),
                "agentId": word(out, 1),
                "counterpartyId": word(out, 2),
                "actionClass": word(out, 3),
                "tier": word(out, 4),
                "valueWei": str(word(out, 5)),
                "outcome": word(out, 6),
                "dataHash": word_hex(out, 7),
                "timestamp": word(out, 8),
                "recorder": "0x" + word_hex(out, 9)[-40:],
            }
        )
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", default="http://127.0.0.1:8547")
    ap.add_argument("--memory", required=True, help="alamat kontrak EconomicMemory")
    args = ap.parse_args()
    print(json.dumps(get_entries(args.rpc, args.memory), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
