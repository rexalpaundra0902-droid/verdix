#!/usr/bin/env bash
# Bootstrap Verdix Phase 1 di BSC TESTNET (chain 97) — one-shot.
# Deploy stack → bikin+fund key agent → register 2 agent → escrow task →
# payment → dogfood journal bot (read-only) → export + Trust Score.
# Hasil: deployments/bsc-testnet.json + deployments/out/
set -euo pipefail
export PATH="$PATH:/root/.foundry/bin"
cd "$(dirname "$0")/.."

RPC=https://bsc-testnet.bnbchain.org
KEYDIR=/root/.verdix-keys
DEPLOYER_PK=$(cat $KEYDIR/testnet-deployer.key)
JOURNAL_DB="${1:-/root/smc-bot-v19/data/journal_testnet.db}"
OUT=deployments/out
mkdir -p deployments "$OUT"

newkey() { # newkey <file> → simpan pk, echo address
  if [[ ! -f "$KEYDIR/$1" ]]; then
    cast wallet new | awk '/Private key/ {print $3}' > "$KEYDIR/$1"
    chmod 600 "$KEYDIR/$1"
  fi
  cast wallet address "$(cat "$KEYDIR/$1")"
}

echo "== 1. deploy stack =="
DEPLOY_LOG=$(forge script script/Deploy.s.sol --rpc-url $RPC --private-key "$DEPLOYER_PK" --broadcast --legacy 2>&1)
REGISTRY=$(echo "$DEPLOY_LOG" | awk '/AgentRegistry :/ {print $NF}')
MEMORY=$(echo "$DEPLOY_LOG"   | awk '/EconomicMemory:/ {print $NF}')
ROUTER=$(echo "$DEPLOY_LOG"   | awk '/PaymentRouter :/ {print $NF}')
ESCROW=$(echo "$DEPLOY_LOG"   | awk '/TaskEscrow    :/ {print $NF}')
ORACLE=$(echo "$DEPLOY_LOG"   | awk '/StressOracle  :/ {print $NF}')
[[ -n "$REGISTRY" && -n "$MEMORY" && -n "$ORACLE" ]] || { echo "DEPLOY GAGAL"; echo "$DEPLOY_LOG" | tail -30; exit 1; }
echo "registry=$REGISTRY memory=$MEMORY router=$ROUTER escrow=$ESCROW oracle=$ORACLE"

echo "== 2. key agent (bot + client) + funding kecil =="
BOT_ADDR=$(newkey bot-agent.key);    BOT_PK=$(cat $KEYDIR/bot-agent.key)
CLI_ADDR=$(newkey client-agent.key); CLI_PK=$(cat $KEYDIR/client-agent.key)
echo "bot=$BOT_ADDR client=$CLI_ADDR"
cast send "$BOT_ADDR" --value 0.05ether --private-key "$DEPLOYER_PK" --rpc-url $RPC --legacy >/dev/null
cast send "$CLI_ADDR" --value 0.05ether --private-key "$DEPLOYER_PK" --rpc-url $RPC --legacy >/dev/null

echo "== 3. register agents (ERC-8004 NFT) =="
cast send "$REGISTRY" "register(string)" "https://smc-bot.agents.verdix.io/agent.json" --private-key "$BOT_PK" --rpc-url $RPC --legacy >/dev/null
cast send "$REGISTRY" "register(string)" "https://reku.agents.verdix.io/agent.json" --private-key "$CLI_PK" --rpc-url $RPC --legacy >/dev/null
BOT_ID=1; CLIENT_ID=2
echo "smc-bot=agentId $BOT_ID, reku=agentId $CLIENT_ID"

echo "== 4. escrow task Tier2 (0.01 tBNB, bond 0.001 dua sisi) =="
DEADLINE=$(( $(cast block latest --field timestamp --rpc-url $RPC) + 86400 ))
SPEC=$(cast keccak "analisis pasar 4H + sinyal harian")
cast send "$ESCROW" "createTask(uint256,uint256,uint128,uint64,bytes32)" \
  $CLIENT_ID $BOT_ID 10000000000000000 $DEADLINE "$SPEC" \
  --value 0.011ether --private-key "$CLI_PK" --rpc-url $RPC --legacy >/dev/null
cast send "$ESCROW" "acceptTask(uint256)" 1 --value 0.001ether --private-key "$BOT_PK" --rpc-url $RPC --legacy >/dev/null
cast send "$ESCROW" "confirm(uint256)" 1 --private-key "$CLI_PK" --rpc-url $RPC --legacy >/dev/null
echo "task 1 confirmed"

echo "== 5. payment Tier1 (0.005 tBNB) =="
cast send "$ROUTER" "pay(uint256,uint256,bytes32)" $CLIENT_ID $BOT_ID \
  "$(cast keccak 'invoice-signal-juli')" \
  --value 0.005ether --private-key "$CLI_PK" --rpc-url $RPC --legacy >/dev/null

echo "== 6. dogfood journal bot (read-only) → Class 4 on-chain =="
python3 dogfood/record_trades.py --db "$JOURNAL_DB" > "$OUT/attestations.json"
python3 - "$OUT/attestations.json" > "$OUT/att_lines.txt" <<'EOF'
import json, sys
for a in json.load(open(sys.argv[1])):
    print(a["valueWei"], str(a["positiveOutcome"]).lower(), a["dataHash"])
EOF
N_ATT=0
while read -r VALUE POSITIVE HASH; do
  cast send "$ORACLE" "attest(uint256,uint128,bool,bytes32)" $BOT_ID "$VALUE" "$POSITIVE" "$HASH" \
    --private-key "$DEPLOYER_PK" --rpc-url $RPC --legacy >/dev/null
  N_ATT=$((N_ATT + 1))
done < "$OUT/att_lines.txt"
echo "$N_ATT trades di-attest"

echo "== 7. export + Trust Intelligence =="
python3 demo/export_entries.py --rpc $RPC --memory "$MEMORY" \
  --registry "$REGISTRY" --rotations-out "$OUT/rotations.json" > "$OUT/entries.json"
python3 intel/trustscore.py "$OUT/entries.json" --agent $BOT_ID --name "smc-bot" \
  --rotations "$OUT/rotations.json" | tee "$OUT/economic_cv_bot.md"

cat > deployments/bsc-testnet.json <<JSON
{
  "chainId": 97,
  "rpc": "$RPC",
  "explorer": "https://testnet.bscscan.com",
  "deployer": "$(cast wallet address "$DEPLOYER_PK")",
  "contracts": {
    "AgentRegistry": "$REGISTRY",
    "EconomicMemory": "$MEMORY",
    "PaymentRouter": "$ROUTER",
    "TaskEscrow": "$ESCROW",
    "StressOracle": "$ORACLE"
  },
  "agents": {
    "1": {"name": "smc-bot", "address": "$BOT_ADDR"},
    "2": {"name": "reku", "address": "$CLI_ADDR"}
  }
}
JSON
echo "== DONE — deployments/bsc-testnet.json =="