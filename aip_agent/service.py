#!/usr/bin/env python3
"""Verdix SMC Bot — agent service di jaringan Unibase AIP/BitAgent.

Polling gateway untuk job `market_signal_4h`, jawab dengan analisis market
structure 4H riil (data Binance publik), lalu:
  1. hasil + konteks di-hash (sha256) → payload diupload ke MEMBASE
     (decentralized memory — job yang dilayani jadi bagian memory immortal agent)
  2. `memory_ref` dikembalikan di result → siapa pun bisa verifikasi via
     Reputation API Verdix: GET /memory/<memory_ref>
  3. Trust Score agent (dihitung dari Economic Memory on-chain) ikut di result

Identity agent: ERC-8004 NFT #1700 di AIP Registry (chain 97) + agentId #1
di Verdix AgentRegistry — satu agent, dua registry, satu reputasi.
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from payloads.membase_store import sha256_hex, upload_payload  # noqa: E402

GATEWAY = os.environ.get("GATEWAY_URL", "https://gateway.aip.unibase.com")
HANDLE = "verdix-smc-bot"
AGENT_ID = "97:0x8004a818bfb912233c491871b3d84c89a494bd9e:1700"
VERDIX_API = os.environ.get("VERDIX_API", "http://127.0.0.1:8600")
BINANCE = "https://api.binance.com"


# ---------- signal engine: 4H market structure ----------

def ema(vals: list[float], n: int) -> float:
    k = 2.0 / (n + 1)
    e = vals[0]
    for v in vals[1:]:
        e = v * k + e * (1 - k)
    return e


def signal_4h(symbol: str) -> dict:
    r = requests.get(
        f"{BINANCE}/api/v3/klines",
        params={"symbol": symbol, "interval": "4h", "limit": 120},
        timeout=15,
    )
    r.raise_for_status()
    kl = r.json()
    closes = [float(k[4]) for k in kl]
    highs = [float(k[2]) for k in kl]
    lows = [float(k[3]) for k in kl]
    last = closes[-1]
    e20, e50 = ema(closes, 20), ema(closes, 50)

    if last > e20 > e50:
        regime, bias = "BULL", "long-continuation"
    elif last < e20 < e50:
        regime, bias = "BEAR", "short-continuation"
    else:
        regime, bias = "RANGE", "wait-for-structure"

    # swing levels sederhana: ekstrem 30 candle terakhir + midpoint
    swing_high = max(highs[-30:])
    swing_low = min(lows[-30:])
    return {
        "symbol": symbol,
        "last_price": last,
        "regime": regime,
        "bias": bias,
        "key_levels": {
            "swing_high_30x4h": swing_high,
            "swing_low_30x4h": swing_low,
            "mid": (swing_high + swing_low) / 2,
            "ema20_4h": round(e20, 8),
            "ema50_4h": round(e50, 8),
        },
        "candles_used": len(closes),
    }


def trust_score() -> dict:
    try:
        d = requests.get(f"{VERDIX_API}/agent/1", timeout=10).json()
        return {"trustScore": d.get("trustScore"), "n_verified_actions": d.get("n_subject")}
    except Exception:
        return {"trustScore": None}


def extract_symbol(task: dict) -> str:
    text = json.dumps(task)
    m = re.search(r"\b([A-Z]{2,10}USDT)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b(BTC|ETH|BNB|SOL|ADA|XRP|DOGE|AVAX|ARB|LINK)\b", text, re.I)
    return (m.group(1).upper() + "USDT") if m else "BTCUSDT"


# ---------- gateway loop ----------

def heartbeat_loop():
    while True:
        try:
            requests.post(
                f"{GATEWAY}/gateway/agents/heartbeat",
                json={"handle": HANDLE, "agent_id": AGENT_ID, "status": "idle",
                      "current_task": None, "metadata": {"verdix_api": VERDIX_API}},
                timeout=10,
            )
        except Exception as e:
            print(f"heartbeat err: {e}", flush=True)
        time.sleep(30)


def handle_task(task: dict) -> dict:
    symbol = extract_symbol(task)
    sig = signal_4h(symbol)
    result = {**sig, "verdix": trust_score()}

    # job yang dilayani → memory immortal: payload ke Membase, ref = sha256
    payload_str = json.dumps(
        {"type": "verdix-aip-job", "task_id": task.get("task_id"),
         "task": task, "result": result, "served_at": int(time.time())},
        sort_keys=True, default=str,
    )
    ref = sha256_hex(payload_str)
    try:
        upload_payload(ref, payload_str)
        result["memory_ref"] = ref
        result["verify_url"] = f"{os.environ.get('VERDIX_PUBLIC_API', 'http://194.233.93.155:8600')}/memory/{ref}"
    except Exception as e:
        print(f"membase upload err: {e}", flush=True)
        result["memory_ref"] = None
    return result


def _process(kind: str, item: dict) -> None:
    """kind: 'job' (jobs/poll, karena kita punya job_offerings) atau 'task'."""
    item_id = item.get("job_id") or item.get("task_id")
    print(f"{kind} masuk: {item_id}", flush=True)
    t0 = time.time()
    try:
        result = handle_task(item)
        status, error = "completed", None
    except Exception as e:
        result, status, error = {}, "failed", str(e)
    if kind == "job":
        body = {"job_id": item_id, "agent_id": HANDLE, "status": status,
                "result": result, "error": error,
                "deliverable_data": {"text": json.dumps(result, default=str)}}
        url = f"{GATEWAY}/gateway/jobs/complete"
    else:
        body = {"task_id": item_id, "status": status, "result": result,
                "error": error, "execution_time": time.time() - t0}
        url = f"{GATEWAY}/gateway/tasks/complete"
    resp = requests.post(url, json=body, timeout=15)
    print(f"{kind} {item_id} -> {status} ({time.time()-t0:.1f}s) "
          f"complete_http={resp.status_code} {resp.text[:120]}", flush=True)


def main() -> int:
    print(f"verdix-aip-agent start — gateway={GATEWAY} handle={HANDLE}", flush=True)
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    while True:
        # poll dua antrian: jobs (offering marketplace) prioritas, tasks fallback
        for kind, path, key in (("job", "jobs", "job_id"), ("task", "tasks", "task_id")):
            try:
                r = requests.get(
                    f"{GATEWAY}/gateway/{path}/poll",
                    params={"agent": HANDLE, "timeout": 15},
                    timeout=25,
                )
                r.raise_for_status()
                item = r.json() if r.content else {}
                if item and item.get(key):
                    _process(kind, item)
            except requests.Timeout:
                continue
            except Exception as e:
                print(f"poll {path} err: {e}", flush=True)
                time.sleep(5)


if __name__ == "__main__":
    raise SystemExit(main())
