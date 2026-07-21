#!/bin/bash
# Aktivasi route berbayar x402 setelah sign-in awal.
# Pakai: bash /root/verdix/x402/activate.sh
set -euo pipefail

ADDR=$(npx awal@2.12.0 address --json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
a=(d.get('data') or d).get('evm') or (d.get('data') or d).get('address') or ''
print(a)")
if [[ ! "$ADDR" =~ ^0x[0-9a-fA-F]{40}$ ]]; then
  echo "❌ Gagal ambil address EVM dari awal — sudah sign-in? (npx awal auth login <email>)"
  npx awal@2.12.0 status || true
  exit 1
fi
sed -i "s/^X402_PAY_TO=.*/X402_PAY_TO=$ADDR/" /root/.verdix-keys/x402.env
systemctl restart verdix-x402
sleep 2
echo "✅ PAY_TO=$ADDR"
curl -s https://verdix-api.kilatlab.com/x402/health
echo
curl -s -o /dev/null -w "paid route status: %{http_code} (402 = LIVE menerima pembayaran)\n" \
  https://verdix-api.kilatlab.com/x402/agent/1
