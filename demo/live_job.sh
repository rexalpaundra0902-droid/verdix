#!/usr/bin/env bash
# Demo step 4 — kirim job LIVE ke verdix-smc-bot lewat Unibase Gateway.
# Pakai: bash demo/live_job.sh [SYMBOL]   (default BTCUSDT)
set -euo pipefail
SYMBOL="${1:-BTCUSDT}"
GATEWAY=https://gateway.aip.unibase.com
JOB="demo-$(date +%s)"

echo "▶ submitting job to Unibase Gateway: '$SYMBOL signal' → verdix-smc-bot (ERC-8004 #1700)"
curl -s -X POST $GATEWAY/gateway/jobs/submit -H "Content-Type: application/json" -d "{
  \"job_id\": \"$JOB\",
  \"agent_id\": \"verdix-smc-bot\",
  \"offering_id\": \"market_signal_4h\",
  \"client_id\": \"demo-client\",
  \"job_input\": \"$SYMBOL signal\"
}" >/dev/null
echo "▶ job accepted: $JOB — waiting for the agent..."

for _ in $(seq 1 30); do
  sleep 2
  BODY=$(curl -s "$GATEWAY/gateway/jobs/$JOB")
  STATUS=$(echo "$BODY" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status'))")
  [ "$STATUS" != "pending" ] && break
done

echo "$BODY" | python3 -c "
import json, sys
d = json.load(sys.stdin)
r = (d.get('metadata') or {}).get('result') or {}
v = r.get('verdix') or {}
print()
print('══════════ VERDIX SMC BOT — LIVE RESULT ══════════')
print(f\"  status      : {d.get('status')}\")
print(f\"  symbol      : {r.get('symbol')}  @ {r.get('last_price')}\")
print(f\"  regime      : {r.get('regime')}  |  bias: {r.get('bias')}\")
kl = r.get('key_levels') or {}
print(f\"  key levels  : H {kl.get('swing_high_30x4h')}  /  L {kl.get('swing_low_30x4h')}\")
print(f\"  trust score : {v.get('trustScore')} / 100  ({v.get('n_verified_actions')} verified on-chain actions)\")
print(f\"  memory_ref  : {r.get('memory_ref')}\")
print()
print('  ▶ verify this job in decentralized memory (Membase):')
print(f\"    {r.get('verify_url')}\")
print('══════════════════════════════════════════════════')
"