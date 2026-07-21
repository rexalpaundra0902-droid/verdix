#!/usr/bin/env bash
# RiskGuardVault live demo di BSC testnet:
# deploy → authorize recorder → policy → deposit → aksi compliant (tercatat di
# Economic Memory) → aksi MELANGGAR (mined sebagai Fail di explorer = bukti
# policy enforcement on-chain) → rescore.
set -euo pipefail
export PATH="$PATH:/root/.foundry/bin"
cd "$(dirname "$0")/.."

RPC=https://bsc-testnet.bnbchain.org
KEYDIR=/root/.verdix-keys
DEPLOYER_PK=$(cat $KEYDIR/testnet-deployer.key)
BOT_PK=$(cat $KEYDIR/bot-agent.key)
VENUE=$(cast wallet address "$(cat $KEYDIR/client-agent.key)") # stand-in venue
REGISTRY=0x5cC6f74214FbD3D390E3be73aBCfc9fb1A41036C
MEMORY=0x6329a6e3920EBA211808a103662136772ad20510
BOT_ID=1
OUT=deployments/out

send() {
  for i in 1 2 3 4; do
    if cast send "$@" --rpc-url $RPC --legacy >/dev/null 2>/tmp/vdx_err; then return 0; fi
    grep -q "nonce too low" /tmp/vdx_err && sleep 4 && continue
    cat /tmp/vdx_err; return 1
  done
  cat /tmp/vdx_err; return 1
}

echo "== 1. deploy RiskGuardVault =="
# policy: maxTx 0.005 | dailyCap 0.01 | cooldown 30s | haltFloor 0.02 (tBNB)
VAULT=$(forge create src/RiskGuardVault.sol:RiskGuardVault \
  --rpc-url $RPC --private-key "$DEPLOYER_PK" --legacy --broadcast \
  --constructor-args $REGISTRY $MEMORY $BOT_ID "(5000000000000000,10000000000000000,30,20000000000000000)" \
  2>&1 | awk '/Deployed to:/ {print $3}')
[[ -n "$VAULT" ]] || { echo "deploy vault gagal"; exit 1; }
echo "vault=$VAULT"
sleep 2

echo "== 2. authorize recorder + whitelist venue + deposit 0.05 =="
send "$MEMORY" "setRecorder(address,bool)" "$VAULT" true --private-key "$DEPLOYER_PK"
sleep 2
send "$VAULT" "setTarget(address,bool)" "$VENUE" true --private-key "$DEPLOYER_PK"
sleep 2
send "$VAULT" --value 0.05ether --private-key "$DEPLOYER_PK"
sleep 2

echo "== 3. aksi COMPLIANT: 0.004 ke venue whitelist =="
OK_TX=$(cast send "$VAULT" "act(address,uint256,bytes32)" "$VENUE" 4000000000000000 \
  "$(cast keccak 'open-position-demo')" \
  --private-key "$BOT_PK" --rpc-url $RPC --legacy --json | python3 -c "import json,sys;print(json.load(sys.stdin)['transactionHash'])")
echo "compliant tx: $OK_TX"
sleep 35  # tunggu cooldown 30s lewat, biar penolakan berikutnya murni soal maxTx

echo "== 4. aksi MELANGGAR: 0.006 > maxTx 0.005 → harus Fail on-chain =="
BAD_TX=$(cast send "$VAULT" "act(address,uint256,bytes32)" "$VENUE" 6000000000000000 \
  "$(cast keccak 'oversize-attempt')" \
  --private-key "$BOT_PK" --rpc-url $RPC --legacy --gas-limit 200000 --json 2>/dev/null \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['transactionHash'])" || true)
echo "blocked tx: ${BAD_TX:-'(revert saat estimasi)'}"
STATUS=$(cast receipt "${BAD_TX}" --field status --rpc-url $RPC 2>/dev/null || echo "?")
echo "status blocked tx: $STATUS (0 = Fail = policy menolak)"

echo "== 5. rescore dari chain =="
python3 demo/export_entries.py --rpc $RPC --memory $MEMORY \
  --registry $REGISTRY --rotations-out "$OUT/rotations.json" > "$OUT/entries.json"
python3 intel/trustscore.py "$OUT/entries.json" --agent $BOT_ID --name "smc-bot" \
  --rotations "$OUT/rotations.json" --json | python3 -c "import json,sys;d=json.load(sys.stdin);print('TrustScore smc-bot:',d['trustScore'],'| entries subjek:',d['n_subject'])"

python3 - "$VAULT" "$OK_TX" "${BAD_TX:-}" <<'EOF'
import json, sys
d = json.load(open("deployments/bsc-testnet.json"))
d["contracts"]["RiskGuardVault"] = sys.argv[1]
d["demo"] = {"compliantTx": sys.argv[2], "blockedTx": sys.argv[3]}
json.dump(d, open("deployments/bsc-testnet.json", "w"), indent=2)
EOF
echo "== DONE =="