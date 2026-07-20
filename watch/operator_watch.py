#!/usr/bin/env python3
"""Watcher operator baru — READ-ONLY, notif Telegram.

Konteks: outreach beta 2026-07-21 nyebar (DM Lucas, DM X @Unibase_AI, post TG
BNB Hack). Begitu ada yang kecantol dan self-serve, ini yang bunyi.

Dicek tiap run (cron 10 menit), murni eth_call ke BSC testnet:
  1. AgentRegistry.agentCount()  — agent baru register → notif id+owner+profil
  2. VaultFactory.vaultCount()   — vault baru dibuat  → notif
Notif HANYA saat angka naik. Tidak menulis apa pun kecuali state file sendiri.
RPC publik suka flaky → gagal baca = skip senyap, coba lagi run berikutnya.
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path

STATE = Path(__file__).with_name(".operator_state.json")
BOT_ENV = Path("/root/smc-bot-v19/.env")
CAST = "/root/.foundry/bin/cast"
RPC = "https://bsc-testnet.bnbchain.org"
REGISTRY = "0x03E3701c98CFe457460BDe6b71d9b466CDC6cBe0"
FACTORY = "0x5883Bb4f6764D738304E9cc621e54b8B157775e4"


def tg(text: str) -> None:
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


def call(to: str, sig: str, *args: str) -> str | None:
    r = subprocess.run(
        [CAST, "call", to, sig, *args, "--rpc-url", RPC],
        capture_output=True, text=True, timeout=30)
    return r.stdout.strip() if r.returncode == 0 else None


def as_int(v: str | None) -> int | None:
    try:
        return int(v, 16) if v and v.startswith("0x") else int(v)
    except (TypeError, ValueError):
        return None


def main() -> int:
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    agents = as_int(call(REGISTRY, "agentCount()(uint256)"))
    vaults = as_int(call(FACTORY, "vaultCount()(uint256)"))

    lines = []
    prev_a = state.get("agents")
    if agents is not None and prev_a is not None and agents > prev_a:
        for aid in range(prev_a + 1, agents + 1):
            owner = call(REGISTRY, "ownerOf(uint256)(address)", str(aid)) or "?"
            badge = " 🏅 FOUNDING OPERATOR" if aid <= 7 else ""
            lines.append(
                f"agent #{aid} register!{badge}\n  owner {owner}\n"
                f"  https://verdix.pages.dev/web/agent/{aid}")
    prev_v = state.get("vaults")
    if vaults is not None and prev_v is not None and vaults > prev_v:
        lines.append(f"vault baru dibuat: {prev_v} → {vaults} total")

    if agents is not None:
        state["agents"] = agents
    if vaults is not None:
        state["vaults"] = vaults
    STATE.write_text(json.dumps(state))

    if lines:
        tg("🎣 VERDIX — ADA YANG KECANTOL\n" + "\n".join(lines)
           + "\nSambut + tagih feedback: where does it break?")
        print("notified:", lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
