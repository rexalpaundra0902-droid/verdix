#!/usr/bin/env bash
# Lanjutan bootstrap BSC testnet (deploy sudah sukses, nonce race di funding).
# Retry-aware: tiap tx dicoba max 4x dengan jeda, aman utk RPC publik yang lag.
set -euo pipefail
export PATH="$PATH:/root/.foundry/bin"
cd "$(dirname "$0")/.."

RPC=https://bsc-testnet.bnbchain.org
KEYDIR=/root/.verdix-keys
DEPLOYER_PK=$(cat $KEYDIR/testnet-deployer.key)
BOT_PK=$(cat $KEYDIR/bot-agent.key)
CLI_PK=$(cat $KEYDIR/client-agent.key)
BOT_ADDR=$(cast wallet address "$BOT_PK")
CLI_ADDR=$(cast wallet address "$CLI_PK")
JOURNAL_DB="${1:-/root/smc-bot-v19/data/journal_testnet.db}"
OUT=deployments/out
mkdir -p "$OUT"

REGISTRY=0x5cC6f74214FbD3D390E3be73aBCfc9fb1A41036C
MEMORY=0x6329a6e3920EBA211808a103662136772ad20510
ROUTER=0xA5e1Ab0ED4dE13Dc5E605296ebE7a2b3Da57f094
ESCROW=0x2D7C9Ffe8Ea86E434442CEE63AE2Aa5C3741B5Ca
ORACLE=0xB272346911f0604930215AF84Bee374A2c5327DF

send() { # send <args...> — retry nonce race
  for i in 1 2 3 4; do
    if cast send "$@" --rpc-url $RPC --legacy >/dev/null 2>/tmp/vdx_err; then return 0; fi
    grep -q "nonce too low" /tmp/vdx_err && sleep 4 && continue
    cat /tmp/vdx_err; return 1
  done
  cat /tmp/vdx_err; return 1
}

echo "== fund client =="
send "$CLI_ADDR" --value 0.05ether --private-key "$DEPLOYER_PK"
sleep 2

echo "== register agents =="
if [[ $(cast call "$REGISTRY" "agentCount()(uint256)" --rpc-url $RPC) == "0" ]]; then
  send "$REGISTRY" "register(string)" "https://smc-bot.agents.verdix.io/agent.json" --private-key "$BOT_PK"
  sleep 2
  send "$REGISTRY" "register(string)" "https://reku.agents.verdix.io/agent.json" --private-key "$CLI_PK"
  sleep 2
fi
BOT_ID=1; CLIENT_ID=2
echo "agentCount=$(cast call "$REGISTRY" "agentCount()(uint256)" --rpc-url $RPC)"

echo "== escrow task Tier2 =="
DEADLINE=$(( $(cast block latest --field timestamp --rpc-url $RPC) + 86400 ))
SPEC=$(cast keccak "analisis pasar 4H + sinyal harian")
send "$ESCROW" "createTask(uint256,uint256,uint128,uint64,bytes32)" \
  $CLIENT_ID $BOT_ID 10000000000000000 $DEADLINE "$SPEC" --value 0.011ether --private-key "$CLI_PK"
sleep 2
send "$ESCROW" "acceptTask(uint256)" 1 --value 0.001ether --private-key "$BOT_PK"
sleep 2
send "$ESCROW" "confirm(uint256)" 1 --private-key "$CLI_PK"
sleep 2
echo "task 1 confirmed"

echo "== payment Tier1 =="
send "$ROUTER" "pay(uint256,uint256,bytes32)" $CLIENT_ID $BOT_ID \
  "$(cast keccak 'invoice-signal-juli')" --value 0.005ether --private-key "$CLI_PK"
sleep 2

echo "== dogfood journal bot =="
python3 dogfood/record_trades.py --db "$JOURNAL_DB" > "$OUT/attestations.json"
python3 - "$OUT/attestations.json" > "$OUT/att_lines.txt" <<'EOF'
import json, sys
for a in json.load(open(sys.argv[1])):
    print(a["valueWei"], str(a["positiveOutcome"]).lower(), a["dataHash"])
EOF
N_ATT=0
while read -r VALUE POSITIVE HASH; do
  send "$ORACLE" "attest(uint256,uint128,bool,bytes32)" $BOT_ID "$VALUE" "$POSITIVE" "$HASH" --private-key "$DEPLOYER_PK"
  sleep 1
  N_ATT=$((N_ATT + 1))
done < "$OUT/att_lines.txt"
echo "$N_ATT trades di-attest"

echo "== export + Trust Intelligence =="
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
echo "== DONE =="