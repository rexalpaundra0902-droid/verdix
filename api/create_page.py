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
TOPIC_REGISTERED = "0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a"
TOPIC_VAULTCREATED = "0xd5e73287491bc3aad84e3f2b12aaae343456ebe03e53454598b05a273edfa7d6"

BODY = """
<p><a href='/web'>&larr; directory</a></p>
<h1>Create Your Verified Agent Vault</h1>
<p class='sub'>Your own non-custodial vault: your AI agent can trade,
but can never break policy — and every action becomes a verifiable
on-chain track record. BSC Testnet (chain 97).</p>

<p class='sub'>No wallet extension? <a href='#' onclick='return vdxWC()'>Connect with WalletConnect (QR) →</a> <span id='wcout' class='mono'></span></p>

<div class='card'><b>How to use — zero to verified agent in ~5 minutes</b>
<ol class='guide'>
<li>Prepare a wallet — a browser extension (MetaMask etc.) or your phone via the WalletConnect (QR) link above. Gas uses free test BNB: <a href='https://www.bnbchain.org/en/testnet-faucet' target='_blank' rel='noopener'>faucet</a></li>
<li>Register your agent (Step 1). The URI is optional metadata — a URL describing your agent; it can stay empty. The wallet that registers becomes the agent's controller, and your agent ID appears automatically.</li>
<li>Create the vault (Step 2). Every field is a hard rule the contract will enforce:
<ul class='guide-defs'>
<li>Max per action — the most the agent may spend in a single transaction.</li>
<li>Daily cap — total spend allowed per rolling 24-hour window.</li>
<li>Cooldown — minimum seconds the agent must wait between actions.</li>
<li>Halt floor — if an action would drop the balance below this, it is blocked.</li>
<li>Initial deposit — BNB you fund the vault with now; you can deposit or withdraw any time later.</li>
</ul></li>
<li>Open your vault page (the link appears right after creation) and whitelist at least one target address — the agent can ONLY send funds to whitelisted destinations, so without this step it cannot act at all.</li>
<li>Let your agent act: the controller wallet calls act(target, value, memo) — a ready-to-paste code snippet is on your vault page. Compliant actions execute; violations revert on-chain.</li>
<li>Watch the reputation build: every compliant action lands in Economic Memory and updates your agent's public profile and Trust Score automatically. No reports to write.</li>
</ol>
<p class='sub' style='margin:12px 0 0'>Stuck? <a href='https://github.com/rexalpaundra0902-droid/verdix/issues' target='_blank' rel='noopener'>Open an issue</a> — beta operators get direct support.</p>
</div>

<div class='card'><b>See it with real numbers — this exact example is live on-chain</b>
<p class='sub'>A vault with policy: max 0.005 BNB per action · 0.01 daily cap · 30s cooldown · 0.02 halt floor. Two actions, two outcomes:</p>
<div class='tblwrap'><table>
<tr><th>The agent tries</th><th>The chain answers</th><th>Proof</th></tr>
<tr><td>send 0.004 BNB to a whitelisted venue — inside every limit</td><td>✅ executed, recorded to Economic Memory, scored</td><td><a href='https://testnet.bscscan.com/tx/0x5ab22b5db269b3b2dd3679fa2af69404d6d0ed1c684f8df79d96a39b532fbc2f' target='_blank' rel='noopener'>tx ↗</a></td></tr>
<tr><td>send 0.006 BNB — just 20% over the 0.005 max</td><td>❌ reverted: ExceedsMaxTx — permanently visible failure</td><td><a href='https://testnet.bscscan.com/tx/0xcb7e5dd10be44df82dfec34f7c49f2fd30be0cd3c57b31b2b6e0a908d34e567d' target='_blank' rel='noopener'>tx ↗</a></td></tr>
</table></div>
<p class='sub' style='margin:10px 0 0'>Every ✅ updates the agent's public profile automatically — see the result on <a href='/web/agent/1'>Agent #1's live profile</a>: score, components, and the full entry log.</p>
<p class='sub'>Both transactions are real. Click them — don't take our word for it.</p>
</div>

<div class='card'><b>Step 1 — Register agent (ERC-8004)</b>
<p class='sub'>Once per agent. The registering wallet becomes the agent's controller.</p>
<input id='uri' placeholder='https://your-agent.example/agent.json'>
<p><button onclick='registerAgent()'>Register Agent</button> <span id='regout' class='mono'></span></p>
</div>

<div class='card'><b>Step 2 — Create vault + policy</b>
<div class='grid'>
<div class='kv'><div class='k'>Agent ID</div><input id='aid' value='1'></div>
<div class='kv'><div class='k'>Max per action (BNB)</div><input id='maxtx' value='0.005'></div>
<div class='kv'><div class='k'>Daily cap (BNB)</div><input id='daily' value='0.01'></div>
<div class='kv'><div class='k'>Cooldown (seconds)</div><input id='cool' value='30'></div>
<div class='kv'><div class='k'>Halt floor (BNB)</div><input id='floor' value='0.02'></div>
<div class='kv'><div class='k'>Initial deposit (BNB)</div><input id='dep' value='0.05'></div>
</div>
<p><button onclick='createVault()'>Create Vault</button> <span id='out' class='mono'></span></p>
</div>

<div class='card'><b>Already have a vault?</b>
<p class='sub'>Enter your wallet address to find every vault you've created.</p>
<input id='lookup' placeholder='0x… your wallet (blank = connected wallet)'>
<p><button onclick='findVaults()'>Find my vaults</button></p>
<div id='vaults' class='mono'></div>
</div>

<div class='card'><b>Step 3 — Manage &amp; use</b>
<p class='sub'>Once the vault is live, manage everything from the browser (deposit,
venue whitelist, withdraw, policy) — no BscScan digging. Your agent calls
<span class='mono'>act(target, value, memo)</span>; every policy-compliant action
automatically becomes a verified track record on your agent's public profile.</p>
<p id='managelink' class='mono'></p>
</div>


<script>
const FACTORY='__FACTORY__', REGISTRY='__REGISTRY__';
const T_REG='__TREG__', T_VAULT='__TVAULT__';
const pad=(h)=>h.replace('0x','').padStart(64,'0');
async function waitReceipt(tx){
  for(let i=0;i<40;i++){
    const r=await ethereum.request({method:'eth_getTransactionReceipt',params:[tx]});
    if(r) return r;
    await new Promise(s=>setTimeout(s,3000));
  }
  return null;
}
function findLog(rcpt,topic0){
  return (rcpt.logs||[]).find(l=>l.topics&&l.topics[0]&&l.topics[0].toLowerCase()===topic0.toLowerCase());
}
async function findVaults(){
  const out=document.getElementById('vaults');
  try{
    let who=document.getElementById('lookup').value.trim();
    if(!who){ who=await ensureChain(); }
    const data='0x6cc811f8'+pad(who.replace('0x','').toLowerCase());
    const res=await ethereum.request({method:'eth_call',params:[{to:FACTORY,data},'latest']});
    const hex=res.replace('0x',''); const n=parseInt(hex.slice(64,128),16);
    if(!n){ out.textContent='No vaults for this wallet.'; return; }
    let html='';
    for(let i=0;i<n;i++){ const a='0x'+hex.slice(128+i*64+24,128+(i+1)*64);
      html+='<div>→ <a href="/web/vault/'+a+'">'+a+'</a></div>'; }
    out.innerHTML=html;
  }catch(e){ out.textContent='err: '+(e.message||e); }
}
// BNB → wei word (presisi via gwei bulat, cukup utk testnet)
const weiWord=(bnb)=>pad((BigInt(Math.round(parseFloat(bnb||'0')*1e9))*1000000000n).toString(16));
async function ensureChain(){
  if(window.__wcActive){ const a=await ethereum.request({method:'eth_accounts'}); return a[0]; }
  await ethereum.request({method:'wallet_addEthereumChain',params:[{chainId:'0x61',chainName:'BSC Testnet',rpcUrls:['https://bsc-testnet.bnbchain.org'],nativeCurrency:{name:'tBNB',symbol:'tBNB',decimals:18},blockExplorerUrls:['https://testnet.bscscan.com']}]}).catch(()=>{});
  await ethereum.request({method:'wallet_switchEthereumChain',params:[{chainId:'0x61'}]});
  const [acc]=await ethereum.request({method:'eth_requestAccounts'});
  return acc;
}
var WC_ID='7c12df52e56bc45ac133a89fc1b3787d';
function vdxWC(){
  var o=document.getElementById('wcout'); o.textContent='loading…';
  var go=function(){ window.__vdxWC(WC_ID).then(function(p){
      window.ethereum=p; window.__wcActive=1;
      var a=p.accounts&&p.accounts[0];
      o.textContent=a?('connected: '+a.slice(0,6)+'…'+a.slice(-4)):'connected';
    }).catch(function(e){o.textContent='err: '+(e.message||e)}); };
  if(window.__vdxWC){go();return false;}
  var s=document.createElement('script'); s.src='/js/wc.js'; s.onload=go;
  s.onerror=function(){o.textContent='failed to load WalletConnect'};
  document.head.appendChild(s); return false;
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
    const o=document.getElementById('regout');
    o.innerHTML='tx sent: <a href="https://testnet.bscscan.com/tx/'+tx+'">'+tx.slice(0,18)+'…</a> — waiting for confirmation…';
    const r=await waitReceipt(tx);
    if(r){ const lg=findLog(r,T_REG);
      if(lg){ const aid=parseInt(lg.topics[1],16);
        document.getElementById('aid').value=aid;
        o.innerHTML='✓ Agent registered — <b>agentId = '+aid+'</b> (filled into Step 2). '
          +'<a href="https://testnet.bscscan.com/tx/'+tx+'">tx</a>';
      } else { o.innerHTML='✓ tx confirmed but Registered event unreadable — check <a href="https://testnet.bscscan.com/tx/'+tx+'">tx</a>'; }
    } else { o.innerHTML='tx not confirmed yet (timeout) — check <a href="https://testnet.bscscan.com/tx/'+tx+'">tx</a>'; }
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
    const o=document.getElementById('out');
    o.innerHTML='tx sent: <a href="https://testnet.bscscan.com/tx/'+tx+'">'+tx.slice(0,18)+'…</a> — waiting for confirmation…';
    const r=await waitReceipt(tx);
    if(r){ const lg=findLog(r,T_VAULT);
      if(lg){ const vault='0x'+lg.topics[1].slice(26);
        o.innerHTML='✓ Vault created: <span class="mono">'+vault+'</span>';
        document.getElementById('managelink').innerHTML=
          '→ <a href="/web/vault/'+vault+'"><b>Manage your vault here</b></a> (deposit, whitelist venues, set policy)';
      } else { o.innerHTML='✓ tx confirmed but VaultCreated event unreadable — check <a href="https://testnet.bscscan.com/tx/'+tx+'">tx</a>'; }
    } else { o.innerHTML='tx not confirmed yet (timeout) — check <a href="https://testnet.bscscan.com/tx/'+tx+'">tx</a>'; }
  }catch(e){document.getElementById('out').textContent='err: '+(e.message||e)}
}
</script>
""".replace("__FACTORY__", FACTORY).replace("__REGISTRY__", REGISTRY) \
   .replace("__SELCREATE__", SEL_CREATE).replace("__SELREG__", SEL_REGISTER) \
   .replace("__TREG__", TOPIC_REGISTERED).replace("__TVAULT__", TOPIC_VAULTCREATED)


def create_page(page_fn) -> str:
    return page_fn("Create Vault — Verdix", BODY,
                   desc="Deploy your own policy-guarded, non-custodial vault in ~5 minutes. "
                        "Your AI agent can trade but can never break policy — every action "
                        "becomes a verifiable on-chain track record.",
                   path="/web/create")
