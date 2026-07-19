#!/usr/bin/env python3
"""Halaman self-serve "Create Your Verified Agent Vault" — /web/create.

Wallet-connect polos (window.ethereum, tanpa library): register agent ERC-8004
lalu deploy GuardedVault milik user sendiri via VaultFactory. Non-custodial:
vault dimiliki wallet user, Verdix tidak pernah memegang dana.
"""

FACTORY = "0x5883Bb4f6764D738304E9cc621e54b8B157775e4"
REGISTRY = "0x03E3701c98CFe457460BDe6b71d9b466CDC6cBe0"
SEL_CREATE = "0x8b89b33e"  # createVault(uint256,(uint128,uint128,uint64,uint128))
SEL_REGISTER = "0xf2c298be"  # register(string)

BODY = """
<p><a href='/web'>&larr; directory</a></p>
<h1>Create Your Verified Agent Vault</h1>
<p class='sub'>Vault non-custodial milikmu sendiri: AI agent-mu bisa trading,
tapi tidak bisa melanggar policy — dan setiap aksinya jadi track record
terverifikasi on-chain. BSC Testnet (chain 97).</p>

<div class='card'><b>Step 1 — Register agent (ERC-8004)</b>
<p class='sub'>Sekali saja per agent. Wallet yang register = controller agent.</p>
<input id='uri' placeholder='https://nama-agent-mu.example/agent.json' style='width:100%;padding:8px;background:#0b0e14;border:1px solid #1c2230;border-radius:8px;color:#e6e9ef'>
<p><button onclick='registerAgent()'>Register Agent</button> <span id='regout' class='mono'></span></p>
</div>

<div class='card'><b>Step 2 — Create vault + policy</b>
<div class='grid'>
<div class='kv'><div class='k'>Agent ID</div><input id='aid' value='1' style='width:100%;padding:6px;background:#0b0e14;border:1px solid #1c2230;border-radius:8px;color:#e6e9ef'></div>
<div class='kv'><div class='k'>Max per aksi (BNB)</div><input id='maxtx' value='0.005' style='width:100%;padding:6px;background:#0b0e14;border:1px solid #1c2230;border-radius:8px;color:#e6e9ef'></div>
<div class='kv'><div class='k'>Cap harian (BNB)</div><input id='daily' value='0.01' style='width:100%;padding:6px;background:#0b0e14;border:1px solid #1c2230;border-radius:8px;color:#e6e9ef'></div>
<div class='kv'><div class='k'>Cooldown (detik)</div><input id='cool' value='30' style='width:100%;padding:6px;background:#0b0e14;border:1px solid #1c2230;border-radius:8px;color:#e6e9ef'></div>
<div class='kv'><div class='k'>Halt floor (BNB)</div><input id='floor' value='0.02' style='width:100%;padding:6px;background:#0b0e14;border:1px solid #1c2230;border-radius:8px;color:#e6e9ef'></div>
<div class='kv'><div class='k'>Deposit awal (BNB)</div><input id='dep' value='0.05' style='width:100%;padding:6px;background:#0b0e14;border:1px solid #1c2230;border-radius:8px;color:#e6e9ef'></div>
</div>
<p><button onclick='createVault()'>Create Vault</button> <span id='out' class='mono'></span></p>
</div>

<div class='card'><b>Step 3 — Kelola &amp; pakai</b>
<p class='sub'>Vault-mu verified di BscScan — whitelist venue (<span class='mono'>setTarget</span>)
dan withdraw lewat tab <i>Write Contract</i>. Agent-mu memanggil
<span class='mono'>act(target, value, memo)</span>; aksi yang lolos policy otomatis
tercatat dan muncul di profil publik agent-mu di directory.</p>
</div>

<style>button{background:#7aa2ff;color:#0b0e14;font-weight:700;border:0;border-radius:8px;padding:9px 16px;cursor:pointer}button:hover{opacity:.9}</style>
<script>
const FACTORY='__FACTORY__', REGISTRY='__REGISTRY__';
const pad=(h)=>h.replace('0x','').padStart(64,'0');
// BNB → wei word (presisi via gwei bulat, cukup utk testnet)
const weiWord=(bnb)=>pad((BigInt(Math.round(parseFloat(bnb||'0')*1e9))*1000000000n).toString(16));
async function ensureChain(){
  await ethereum.request({method:'wallet_addEthereumChain',params:[{chainId:'0x61',chainName:'BSC Testnet',rpcUrls:['https://bsc-testnet.bnbchain.org'],nativeCurrency:{name:'tBNB',symbol:'tBNB',decimals:18},blockExplorerUrls:['https://testnet.bscscan.com']}]}).catch(()=>{});
  await ethereum.request({method:'wallet_switchEthereumChain',params:[{chainId:'0x61'}]});
  const [acc]=await ethereum.request({method:'eth_requestAccounts'});
  return acc;
}
async function registerAgent(){
  try{
    const acc=await ensureChain();
    const uri=document.getElementById('uri').value||'';
    const bytes=new TextEncoder().encode(uri);
    let hex=''; bytes.forEach(b=>hex+=b.toString(16).padStart(2,'0'));
    const padded=hex.padEnd(Math.ceil(hex.length/64)*64,'0');
    const data='__SELREG__'+pad('20')+pad(bytes.length.toString(16))+padded;
    const tx=await ethereum.request({method:'eth_sendTransaction',params:[{from:acc,to:REGISTRY,data}]});
    document.getElementById('regout').innerHTML='tx: <a href="https://testnet.bscscan.com/tx/'+tx+'">'+tx.slice(0,18)+'…</a> — agentId = cek event Registered';
  }catch(e){document.getElementById('regout').textContent='err: '+(e.message||e)}
}
async function createVault(){
  try{
    const acc=await ensureChain();
    const aid=BigInt(document.getElementById('aid').value);
    const data='__SELCREATE__'+pad(aid.toString(16))
      +weiWord(document.getElementById('maxtx').value)
      +weiWord(document.getElementById('daily').value)
      +pad(BigInt(document.getElementById('cool').value||'0').toString(16))
      +weiWord(document.getElementById('floor').value);
    const value='0x'+(BigInt(Math.round(parseFloat(document.getElementById('dep').value||'0')*1e9))*1000000000n).toString(16);
    const tx=await ethereum.request({method:'eth_sendTransaction',params:[{from:acc,to:FACTORY,data,value}]});
    document.getElementById('out').innerHTML='tx: <a href="https://testnet.bscscan.com/tx/'+tx+'">'+tx.slice(0,18)+'…</a> — alamat vault ada di event VaultCreated';
  }catch(e){document.getElementById('out').textContent='err: '+(e.message||e)}
}
</script>
""".replace("__FACTORY__", FACTORY).replace("__REGISTRY__", REGISTRY) \
   .replace("__SELCREATE__", SEL_CREATE).replace("__SELREG__", SEL_REGISTER)


def create_page(page_fn) -> str:
    return page_fn("Create Vault — Verdix", BODY)
