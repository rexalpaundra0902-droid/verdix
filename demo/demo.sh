#!/usr/bin/env bash
# Verdix Phase 1 — demo end-to-end di anvil lokal.
#
#   anvil → deploy stack → register 2 agent → escrow task (Tier 2) →
#   payment (Tier 1) → dogfood trade bot SMC (Class 4) → export memory →
#   Trust Score + Economic CV
#
# Pakai: bash demo/demo.sh [path_journal_db]
set -euo pipefail
export PATH="$PATH:/root/.foundry/bin"

cd "$(dirname "$0")/.."
RPC=http://127.0.0.1:8547
JOURNAL_DB="${1:-/root/smc-bot-v19/data/journal_live.db}"
OUT=demo/out
mkdir -p "$OUT"

# Anvil default keys (lokal saja — JANGAN dipakai di jaringan publik)
DEPLOYER_PK=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
BOT_PK=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
CLIENT_PK=0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a

cleanup() { [[ -n "${ANVIL_PID:-}" ]] && kill "$ANVIL_PID" 2>/dev/null || true; }
trap cleanup EXIT

echo "== 1. anvil =="
anvil --port 8547 --silent &
ANVIL_PID=$!
for _ in $(seq 1 50); do
  cast chain-id --rpc-url $RPC >/dev/null 2>&1 && break
  sleep 0.1
done

echo "== 2. deploy stack =="
DEPLOY_LOG=$(forge script script/Deploy.s.sol --rpc-url $RPC --private-key $DEPLOYER_PK --broadcast 2>&1)
REGISTRY=$(echo "$DEPLOY_LOG" | awk '/AgentRegistry :/ {print $NF}')
MEMORY=$(echo "$DEPLOY_LOG"   | awk '/EconomicMemory:/ {print $NF}')
ROUTER=$(echo "$DEPLOY_LOG"   | awk '/PaymentRouter :/ {print $NF}')
ESCROW=$(echo "$DEPLOY_LOG"   | awk '/TaskEscrow    :/ {print $NF}')
ORACLE=$(echo "$DEPLOY_LOG"   | awk '/StressOracle  :/ {print $NF}')
echo "registry=$REGISTRY memory=$MEMORY router=$ROUTER escrow=$ESCROW oracle=$ORACLE"
[[ -n "$REGISTRY" && -n "$MEMORY" && -n "$ORACLE" ]] || { echo "deploy gagal"; echo "$DEPLOY_LOG" | tail -20; exit 1; }

echo "== 3. register agents (ERC-8004: agent = NFT) =="
cast send $REGISTRY "register(string)" "https://smc-bot.agents.verdix.io/agent.json" --private-key $BOT_PK --rpc-url $RPC >/dev/null
cast send $REGISTRY "register(string)" "https://reku.agents.verdix.io/agent.json" --private-key $CLIENT_PK --rpc-url $RPC >/dev/null
BOT_ID=1; CLIENT_ID=2
echo "smc-bot = agentId $BOT_ID, reku = agentId $CLIENT_ID"

echo "== 4. Tier 2: escrow task (client -> bot) =="
DEADLINE=$(( $(cast block latest --field timestamp --rpc-url $RPC) + 3600 ))
SPEC=$(cast keccak "jalankan analisis pasar 4H, deliver sinyal harian")
cast send $ESCROW "createTask(uint256,uint256,uint128,uint64,bytes32)" \
  $CLIENT_ID $BOT_ID 1000000000000000000 $DEADLINE $SPEC \
  --value 1.1ether --private-key $CLIENT_PK --rpc-url $RPC >/dev/null
cast send $ESCROW "acceptTask(uint256)" 1 --value 0.1ether --private-key $BOT_PK --rpc-url $RPC >/dev/null
cast send $ESCROW "confirm(uint256)" 1 --private-key $CLIENT_PK --rpc-url $RPC >/dev/null
echo "task 1: created -> accepted (bond 2 sisi) -> confirmed (2 entries tercatat)"

echo "== 5. Tier 1: direct payment =="
cast send $ROUTER "pay(uint256,uint256,bytes32)" $CLIENT_ID $BOT_ID \
  "$(cast keccak 'invoice-signal-juli')" \
  --value 0.5ether --private-key $CLIENT_PK --rpc-url $RPC >/dev/null
echo "payment 0.5 ETH client -> bot tercatat (settlement = proof)"

echo "== 6. Class 4: dogfood trade journal SMC bot (read-only) =="
python3 dogfood/record_trades.py --db "$JOURNAL_DB" > "$OUT/attestations.json"
python3 - "$OUT/attestations.json" > "$OUT/att_lines.txt" <<'EOF'
import json, sys
for a in json.load(open(sys.argv[1])):
    print(a["valueWei"], str(a["positiveOutcome"]).lower(), a["dataHash"])
EOF
N_ATT=0
while read -r VALUE POSITIVE HASH; do
  cast send $ORACLE "attest(uint256,uint128,bool,bytes32)" $BOT_ID "$VALUE" "$POSITIVE" "$HASH" \
    --private-key $DEPLOYER_PK --rpc-url $RPC >/dev/null
  N_ATT=$((N_ATT + 1))
done < "$OUT/att_lines.txt"
echo "$N_ATT closed trades di-attest sebagai observed behavior under stress"

echo "== 7. export Economic Memory + control changes =="
python3 demo/export_entries.py --rpc $RPC --memory $MEMORY \
  --registry $REGISTRY --rotations-out "$OUT/rotations.json" > "$OUT/entries.json"
echo "$(python3 -c "import json;print(len(json.load(open('$OUT/entries.json'))))") entries -> $OUT/entries.json"

echo "== 8. Trust Intelligence =="
python3 intel/trustscore.py "$OUT/entries.json" --agent $BOT_ID --name "smc-bot" \
  --rotations "$OUT/rotations.json" | tee "$OUT/economic_cv_bot.md"
SCORE_BEFORE=$(python3 intel/trustscore.py "$OUT/entries.json" --agent $BOT_ID \
  --rotations "$OUT/rotations.json" --json | python3 -c "import json,sys;print(json.load(sys.stdin)['trustScore'])")

echo "== 9. anti 'beli reputasi': NFT identity bot dijual =="
BUYER_ADDR=0x90F79bf6EB2c4f870365E785982E1f101E93b906  # anvil #3
BOT_ADDR=$(cast wallet address $BOT_PK)
cast send $REGISTRY "transferFrom(address,address,uint256)" $BOT_ADDR $BUYER_ADDR $BOT_ID \
  --private-key $BOT_PK --rpc-url $RPC >/dev/null
python3 demo/export_entries.py --rpc $RPC --memory $MEMORY \
  --registry $REGISTRY --rotations-out "$OUT/rotations.json" >/dev/null
SCORE_AFTER=$(python3 intel/trustscore.py "$OUT/entries.json" --agent $BOT_ID \
  --rotations "$OUT/rotations.json" --json | python3 -c "import json,sys;print(json.load(sys.stdin)['trustScore'])")
echo "Trust Score bot: $SCORE_BEFORE -> $SCORE_AFTER setelah identity pindah tangan (history lama di-discount)"

echo
echo "== DONE — Verdix Phase 1 hidup di anvil =="
