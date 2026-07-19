#!/usr/bin/env python3
"""Backfill payload store: semua dataHash yang sudah on-chain → upload payload ke Membase.

Sumber payload:
  1. Dogfood trades (sha256) — regenerate dari journal bot (read-only)
  2. Spec/memo escrow & payment & vault (keccak dari string demo yang diketahui)

Jalankan dari root repo dgn venv: .venv/bin/python payloads/backfill.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dogfood.record_trades import load_closed_trades, to_attestations  # noqa: E402
from payloads.membase_store import keccak_hex, upload_payload  # noqa: E402

# String demo yang di-keccak jadi specHash/memo on-chain (lihat script/*.sh)
KNOWN_KECCAK_PAYLOADS = [
    "analisis pasar 4H + sinyal harian",
    "invoice-signal-juli",
    "open-position-demo",
    "oversize-attempt",
]


def main() -> int:
    db = sys.argv[1] if len(sys.argv) > 1 else "/root/smc-bot-v19/data/journal_testnet.db"
    # HARUS sama persis dgn source saat attest on-chain (bootstrap pakai default),
    # kalau tidak hash-nya beda dan payload tidak akan match entry on-chain
    source = sys.argv[2] if len(sys.argv) > 2 else "smc-bot-live"
    ok = fail = 0

    # cross-check: hash regenerasi wajib ada di Economic Memory on-chain
    onchain = set()
    entries_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "deployments", "out", "entries.json")
    if os.path.exists(entries_file):
        onchain = {e["dataHash"].lower() for e in json.load(open(entries_file))}

    for att in to_attestations(load_closed_trades(db), source):
        tag = ""
        if onchain and att["dataHash"].lower() not in onchain:
            print(f"  trade #{att['tradeId']} SKIP: hash tidak ada on-chain (source salah?)")
            fail += 1
            continue
        try:
            upload_payload(att["dataHash"], att["payload"])
            print(f"  trade #{att['tradeId']} {att['symbol']} -> {att['dataHash'][:18]}... OK (on-chain ✓){tag}")
            ok += 1
        except Exception as e:
            print(f"  trade #{att['tradeId']} GAGAL: {e}")
            fail += 1

    for text in KNOWN_KECCAK_PAYLOADS:
        h = keccak_hex(text)
        try:
            upload_payload(h, text)
            print(f"  spec '{text[:30]}' -> {h[:18]}... OK")
            ok += 1
        except Exception as e:
            print(f"  spec '{text[:30]}' GAGAL: {e}")
            fail += 1

    print(json.dumps({"uploaded": ok, "failed": fail}))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
