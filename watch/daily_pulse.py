#!/usr/bin/env python3
"""Verdix daily pulse — bikin agent hidup sendiri, tanpa nunggu disuruh.

Jalan via cron 1x/hari:
  1. Trade closed BARU di journal LIVE MAINNET bot (uang riil) → attest on-chain
     (StressOracle, Class 4) + payload ke Membase. Economic Memory tumbuh sendiri.
     (Sebelum 2026-07-20 sumbernya journal testnet — 8 attestasi awal + state
     "attested" berasal dari sana; sekarang pakai "attested_live".)
  2. Agent nulis jurnal pasar 4H harian (BTC/ETH) ke Membase — memory-nya
     bertambah tiap hari walau tidak ada job masuk.
Incremental (state file), journal dibaca READ-ONLY, tx on-chain di TESTNET (chain 97).
Notif TG singkat kalau ada aktivitas.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STATE = Path(__file__).with_name(".pulse_state.json")
DB = "/root/smc-bot-v19/data/journal_live.db"  # LIVE MAINNET sejak 2026-07-20
SOURCE = "smc-bot-live"  # label historis attestation awal — sekarang beneran live
RPC = "https://bsc-testnet.bnbchain.org"
ORACLE = "0x170a7BdfA4a7A56D816B89537Ba51EA488a70b26"
BOT_AGENT_ID = "1"
KEY_FILE = "/root/.verdix-keys/testnet-deployer.key"
MEMBASE_ENV = "/root/.verdix-keys/verdix-api.env"
CAST = "/root/.foundry/bin/cast"
BOT_ENV = Path("/root/smc-bot-v19/.env")
JOURNAL_SYMBOLS = ["BTCUSDT", "ETHUSDT"]


def load_membase_env() -> None:
    for line in Path(MEMBASE_ENV).read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def tg(text: str) -> None:
    try:
        env = {}
        for line in BOT_ENV.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
        data = json.dumps({"chat_id": env["TELEGRAM_CHAT_ID"], "text": text}).encode()
        urllib.request.urlopen(
            urllib.request.Request(
                f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/sendMessage",
                data=data, headers={"Content-Type": "application/json"},
            ), timeout=15)
    except Exception as e:
        print(f"tg err: {e}")


def attest_onchain(value_wei: str, positive: bool, data_hash: str) -> None:
    key = Path(KEY_FILE).read_text().strip()
    for attempt in range(4):
        r = subprocess.run(
            [CAST, "send", ORACLE, "attest(uint256,uint128,bool,bytes32)",
             BOT_AGENT_ID, value_wei, "true" if positive else "false", data_hash,
             "--private-key", key, "--rpc-url", RPC, "--legacy"],
            capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            return
        if "nonce too low" in r.stderr and attempt < 3:
            time.sleep(4)
            continue
        raise RuntimeError(r.stderr[:200])


def attest_new_trades(state: dict) -> list[str]:
    from dogfood.record_trades import load_closed_trades, to_attestations
    from payloads.membase_store import upload_payload

    # "attested" lama = trade-id journal TESTNET (arsip, jangan dipakai lagi —
    # id live mulai dari 1 juga, bakal nabrak). Live pakai key sendiri.
    done = set(state.setdefault("attested_live", []))
    lines = []
    for a in to_attestations(load_closed_trades(DB), SOURCE):
        if a["tradeId"] in done:
            continue
        try:
            attest_onchain(a["valueWei"], a["positiveOutcome"], a["dataHash"])
            upload_payload(a["dataHash"], a["payload"])
            done.add(a["tradeId"])
            lines.append(f"  trade #{a['tradeId']} {a['symbol']} {a['exitReason']} pnl={a['pnlUsd']}")
            print(f"attested #{a['tradeId']} {a['symbol']} -> {a['dataHash'][:16]}...")
        except Exception as e:
            print(f"GAGAL attest #{a['tradeId']}: {e}")
    state["attested_live"] = sorted(done)
    return lines


def daily_journal() -> str | None:
    """Agent nulis pandangan pasar hariannya sendiri ke Membase."""
    from aip_agent.service import signal_4h
    from payloads.membase_store import sha256_hex, upload_payload

    reads = []
    for sym in JOURNAL_SYMBOLS:
        try:
            reads.append(signal_4h(sym))
        except Exception as e:
            print(f"signal {sym} err: {e}")
    if not reads:
        return None
    payload = json.dumps(
        {"type": "verdix-daily-journal", "agent": "verdix-smc-bot",
         "date": time.strftime("%Y-%m-%d"), "reads": reads},
        sort_keys=True, default=str)
    ref = sha256_hex(payload)
    upload_payload(ref, payload)
    print(f"jurnal harian -> {ref[:16]}...")
    return ref


def main() -> int:
    load_membase_env()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}

    trade_lines = attest_new_trades(state)

    ref = None
    today = time.strftime("%Y-%m-%d")
    if state.get("last_journal") != today:
        ref = daily_journal()
        if ref:
            state["last_journal"] = today
            state["last_journal_ref"] = ref

    STATE.write_text(json.dumps(state))

    if trade_lines or ref:
        msg = "🫀 VERDIX DAILY PULSE\n"
        if trade_lines:
            msg += f"+{len(trade_lines)} trade → Economic Memory (on-chain+Membase):\n" + "\n".join(trade_lines) + "\n"
        if ref:
            msg += f"jurnal pasar harian → Membase: /memory/{ref[:18]}..."
        tg(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
