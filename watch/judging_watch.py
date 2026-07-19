#!/usr/bin/env python3
"""Watcher penjurian Unibase/BNB Hack — READ-ONLY, notif Telegram.

Dicek tiap run (cron 30 menit):
  1. Stats agent di platform AIP (total/completed jobs) — juri interaksi = jobs naik
  2. Status agent di gateway (online? heartbeat stale?)
  3. GitHub repo stars/forks/watchers — tanda direview
  4. Reputation API publik reachable
Notif HANYA saat ada perubahan / masalah; plus ringkasan status kalau
sudah >3 hari senyap total (biar tahu watcher-nya masih hidup).
Tidak menulis apa pun kecuali state file sendiri + kirim TG.
"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

STATE = Path(__file__).with_name(".state.json")
BOT_ENV = Path("/root/smc-bot-v19/.env")
REPO = "rexalpaundra0902-droid/verdix"
HANDLE = "verdix-smc-bot"
QUIET_SUMMARY_SECS = 3 * 86400


def _get(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": "verdix-watch/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def tg(text: str) -> None:
    env = {}
    for line in BOT_ENV.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    data = json.dumps(
        {"chat_id": env["TELEGRAM_CHAT_ID"], "text": text, "disable_web_page_preview": True}
    ).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{env['TELEGRAM_BOT_TOKEN']}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=15)


def snapshot() -> dict:
    s: dict = {"ts": int(time.time()), "problems": []}
    try:
        d = _get(f"https://api.aip.unibase.com/agents/handle/{HANDLE}")
        stats = d.get("stats") or {}
        s["total_jobs"] = int(stats.get("total_jobs") or 0)
        s["completed_jobs"] = int(stats.get("completed_jobs") or 0)
        s["revenue"] = float(stats.get("total_revenue") or 0)
    except Exception as e:
        s["problems"].append(f"platform API: {e}")
    try:
        g = _get(f"https://gateway.aip.unibase.com/gateway/agents/{HANDLE}/stats")
        st = g.get("agent_status") or {}
        s["gw_status"] = st.get("status")
        hb = st.get("last_heartbeat") or ""
        s["gw_heartbeat"] = hb
        s["gw_tasks_completed"] = int(g.get("completed") or 0)
    except Exception as e:
        s["problems"].append(f"gateway: {e}")
    try:
        r = _get(f"https://api.github.com/repos/{REPO}")
        s["stars"] = r.get("stargazers_count", 0)
        s["forks"] = r.get("forks_count", 0)
    except Exception as e:
        s["problems"].append(f"github: {e}")
    try:
        _get("http://127.0.0.1:8600/", timeout=10)
        s["api_ok"] = True
    except Exception:
        s["api_ok"] = False
        s["problems"].append("Reputation API :8600 DOWN")
    return s


def main() -> int:
    old = json.loads(STATE.read_text()) if STATE.exists() else {}
    now = snapshot()
    msgs = []

    for key, label in (("total_jobs", "job masuk ke agent"),
                       ("completed_jobs", "job selesai"),
                       ("gw_tasks_completed", "task gateway selesai"),
                       ("stars", "GitHub star"), ("forks", "GitHub fork")):
        o, n = old.get(key), now.get(key)
        if o is not None and n is not None and n > o:
            msgs.append(f"📈 {label}: {o} → {n}")

    if now.get("gw_status") not in ("idle", "busy", None):
        msgs.append(f"⚠️ status gateway: {now.get('gw_status')}")
    for p in now["problems"]:
        if p not in old.get("problems", []):
            msgs.append(f"🔴 {p}")
    for p in old.get("problems", []):
        if p not in now["problems"]:
            msgs.append(f"✅ pulih: {p}")

    last_ping = old.get("last_ping", 0)
    if msgs:
        tg("🔭 VERDIX JUDGING WATCH\n" + "\n".join(msgs))
        now["last_ping"] = now["ts"]
    elif now["ts"] - last_ping > QUIET_SUMMARY_SECS:
        tg(
            "🔭 VERDIX JUDGING WATCH — senyap, semua sehat\n"
            f"jobs: {now.get('total_jobs')} | stars: {now.get('stars')} | "
            f"agent: {now.get('gw_status')} | API: {'ok' if now.get('api_ok') else 'DOWN'}\n"
            "Belum ada tanda juri. Pertimbangkan follow-up di kanal komunitas."
        )
        now["last_ping"] = now["ts"]
    else:
        now["last_ping"] = last_ping

    STATE.write_text(json.dumps(now, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
