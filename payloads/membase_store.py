#!/usr/bin/env python3
"""Verdix payload store di atas Membase (Unibase DA) — implementasi moat v9.

On-chain (EconomicMemory) hanya menyimpan bukti + `dataHash`.
Payload lengkap di balik tiap hash — spec task, konteks trade, telemetri —
disimpan di Membase hub sebagai `<dataHash>.json`, sehingga:
  - siapa pun bisa VERIFIKASI: sha256(payload) == dataHash on-chain
  - payload persist lintas platform (decentralized memory, bukan file lokal)

Env yang dipakai (identity Membase kita):
  MEMBASE_ID, MEMBASE_ACCOUNT, MEMBASE_SECRET_KEY, MEMBASE_HUB (opsional)
"""

from __future__ import annotations

import hashlib
import json
import os


def _owner() -> str:
    owner = os.environ.get("MEMBASE_ACCOUNT", "")
    if not owner:
        raise RuntimeError("MEMBASE_ACCOUNT belum di-set")
    return owner


def _hub():
    from membase.storage.hub import hub_client

    return hub_client


def sha256_hex(payload_str: str) -> str:
    return "0x" + hashlib.sha256(payload_str.encode()).hexdigest()


def keccak_hex(payload_str: str) -> str:
    from web3 import Web3

    h = Web3.keccak(text=payload_str).hex()
    return h if h.startswith("0x") else "0x" + h


def hash_matches(data_hash: str, payload_str: str) -> bool:
    """dataHash Verdix bisa sha256 (dogfood) atau keccak256 (spec/memo on-chain)."""
    h = data_hash.lower()
    if sha256_hex(payload_str) == h:
        return True
    try:
        return keccak_hex(payload_str).lower() == h
    except Exception:
        return False


def upload_payload(data_hash: str, payload_str: str, wait: bool = True) -> bool:
    """Simpan payload mentah (string persis yang di-hash) sebagai <dataHash>.json."""
    if not hash_matches(data_hash, payload_str):
        raise ValueError(f"payload tidak match hash {data_hash}")
    hub = _hub()
    res = hub.upload_hub(_owner(), f"{data_hash.lower()}.json", payload_str, wait=wait)
    if wait:
        hub.wait_for_upload_queue()
    return bool(res)


def fetch_payload(data_hash: str, owner: str | None = None) -> dict:
    """Ambil payload dari Membase + verifikasi terhadap hash on-chain.

    Return: {dataHash, verified, payload (dict/str) | None}
    """
    hub = _hub()
    raw = hub.download_hub(owner or _owner(), f"{data_hash.lower()}.json")
    if raw is None:
        return {"dataHash": data_hash, "verified": False, "payload": None, "error": "not found in Membase"}
    text = raw.decode()
    verified = hash_matches(data_hash, text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = text
    return {"dataHash": data_hash, "verified": verified, "payload": payload}


if __name__ == "__main__":
    import sys

    print(json.dumps(fetch_payload(sys.argv[1]), indent=2, default=str))
