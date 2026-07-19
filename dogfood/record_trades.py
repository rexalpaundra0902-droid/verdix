#!/usr/bin/env python3
"""Dogfood Verdix: journal SMC bot (READ-ONLY) → Class 4 stress attestations.

Setiap closed trade bot adalah "observed behavior under stress" per spec v8:
- disciplined exit (SL kena sesuai risk plan, TP, trailing) → positiveOutcome
  BUKAN karena profit — karena perilakunya sesuai kontrak risk yang dideklarasikan.
- breakdown (liquidation, manual panic, unknown) → negative.

Output: JSON list siap dikirim StressOracle.attest() oleh attestor.
Tidak pernah menulis apa pun ke journal — koneksi mode=ro.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3

USD_SCALE = 10**15  # 1 USD PnL absolut ≈ 0.001 "ETH-unit" di demo

# exit yang menunjukkan bot mengikuti risk plan-nya sendiri
DISCIPLINED_EXITS = {
    "sl",
    "be",
    "stop_loss",
    "sl_hit",
    "tp",
    "tp1",
    "tp2",
    "take_profit",
    "trailing",
    "trailing_stop",
    "time_stop",
    "breakeven",
    "signal_flip",
    "blackout_close",
}
BREAKDOWN_EXITS = {"liquidation", "liquidated", "adl", "margin_call"}


def classify(exit_reason: str | None) -> bool:
    r = (exit_reason or "").strip().lower()
    if r in BREAKDOWN_EXITS:
        return False
    if r in DISCIPLINED_EXITS:
        return True
    # exit reason tak dikenal = tidak bisa dibuktikan disiplin → negative
    return False


def load_closed_trades(db_path: str) -> list[dict]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id, symbol, side, entry_time, exit_time, exit_reason, "
        "       size_usd, pnl_usd, pnl_pct "
        "FROM trades WHERE exit_time IS NOT NULL ORDER BY exit_time"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def to_attestations(trades: list[dict], source: str) -> list[dict]:
    out = []
    for t in trades:
        positive = classify(t["exit_reason"])
        payload = json.dumps({**t, "source": source}, sort_keys=True, default=str)
        data_hash = "0x" + hashlib.sha256(payload.encode()).hexdigest()
        value_wei = int(abs(float(t["pnl_usd"] or 0.0)) * USD_SCALE)
        out.append(
            {
                "tradeId": t["id"],
                "symbol": t["symbol"],
                "exitReason": t["exit_reason"],
                "pnlUsd": t["pnl_usd"],
                "positiveOutcome": positive,
                "valueWei": str(value_wei),
                "dataHash": data_hash,
                # string persis yang di-hash — dipush ke Membase (payload store v9)
                "payload": payload,
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="path journal sqlite (dibuka read-only)")
    ap.add_argument("--source", default="smc-bot-live")
    args = ap.parse_args()
    trades = load_closed_trades(args.db)
    print(json.dumps(to_attestations(trades, args.source), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
