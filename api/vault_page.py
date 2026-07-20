#!/usr/bin/env python3
"""Halaman kelola vault self-serve — /web/vault/<addr>.

Baca state GuardedVault langsung dari chain (RPC publik, tanpa wallet) lalu
sediakan kontrol owner (deposit / withdraw / whitelist venue / policy / manager)
dan tester aksi agent — semuanya via window.ethereum, tanpa pernah menyuruh
operator ke tab Write Contract BscScan. Non-custodial: Verdix tak pernah pegang
kunci; kontrak sendiri yang menegakkan policy.
"""

RPC = "https://bsc-testnet.bnbchain.org"

# selectors GuardedVault
SEL = {
    "owner": "0x8da5cb5b",
    "managerAgentId": "0x702bd785",
    "policy": "0x0505c8c9",
    "spentInWindow": "0xdb1f237f",
    "windowStart": "0xb0c2783a",
    "lastActionAt": "0xcaa027c0",
    "allowedTarget": "0x5f39f892",
    "withdraw": "0x2e1a7d4d",
    "setTarget": "0x80ffe77f",
    "setPolicy": "0xc95117a0",
    "setManager": "0xd584346d",
    "act": "0xae356b7f",
}


def _body(addr: str) -> str:
    return (
        "<p><a href='/web'>&larr; directory</a> &nbsp;·&nbsp; <a href='/web/create'>+ create another</a></p>"
        "<h1>Manage Vault</h1>"
        f"<p class='sub'>Vault non-custodial-mu di BSC Testnet. State dibaca langsung dari chain — "
        f"kontrol di bawah menegakkan policy on-chain; agent tidak akan pernah bisa melanggarnya.<br>"
        f"<span class='mono' id='addr'>{addr}</span> · "
        f"<a id='scan' href='https://testnet.bscscan.com/address/{addr}'>BscScan</a></p>"

        "<div class='card'>"
        "<button onclick='connect()'>Connect wallet</button> "
        "<span id='who' class='mono'></span>"
        "</div>"

        "<h2>Live state</h2>"
        "<div class='card'><div class='grid' id='state'>"
        "<div class='kv'><div class='k'>Loading…</div></div>"
        "</div>"
        "<p><button onclick='loadState()'>↻ Refresh</button></p></div>"

        "<h2>Owner controls</h2>"
        "<p class='sub' id='ownnote'>Hanya owner vault yang bisa memakai kontrol ini (kontrak menolak yang lain).</p>"

        "<div class='card'><b>Deposit / Withdraw (BNB)</b>"
        "<div class='grid'>"
        "<div class='kv'><div class='k'>Deposit</div><input id='depAmt' value='0.02'>"
        "<p><button onclick='deposit()'>Deposit</button></p></div>"
        "<div class='kv'><div class='k'>Withdraw</div><input id='wAmt' value='0.01'>"
        "<p><button onclick='doWithdraw()'>Withdraw</button></p></div>"
        "</div><span id='fout' class='mono'></span></div>"

        "<div class='card'><b>Whitelist venue (setTarget)</b>"
        "<p class='sub'>Agent hanya boleh mengirim dana ke alamat yang di-whitelist. "
        "Tambah tujuan yang sah (mis. router venue) sebelum agent beraksi.</p>"
        "<div class='grid'>"
        "<div class='kv'><div class='k'>Alamat target</div><input id='tgt' placeholder='0x…'></div>"
        "<div class='kv'><div class='k'>Izinkan?</div>"
        "<select id='tgtAllow' style='width:100%;padding:9px 10px;background:#0a0e18;border:1px solid #1b2232;border-radius:9px;color:#e8ecf4'>"
        "<option value='1'>allow ✓</option><option value='0'>revoke ✕</option></select></div>"
        "</div><p><button onclick='setTarget()'>Set target</button> <span id='tout' class='mono'></span></p></div>"

        "<div class='card'><b>Update policy</b>"
        "<div class='grid'>"
        "<div class='kv'><div class='k'>Max per aksi (BNB)</div><input id='pMax' value='0.005'></div>"
        "<div class='kv'><div class='k'>Cap harian (BNB)</div><input id='pDaily' value='0.01'></div>"
        "<div class='kv'><div class='k'>Cooldown (detik)</div><input id='pCool' value='30'></div>"
        "<div class='kv'><div class='k'>Halt floor (BNB)</div><input id='pFloor' value='0.02'></div>"
        "</div><p><button onclick='setPolicy()'>Set policy</button> <span id='pout' class='mono'></span></p></div>"

        "<div class='card'><b>Ganti manager agent (setManager)</b>"
        "<div class='grid'><div class='kv'><div class='k'>Agent ID (ERC-8004)</div><input id='mAid' value='1'></div></div>"
        "<p><button onclick='setManager()'>Set manager</button> <span id='mout' class='mono'></span></p></div>"

        "<h2>Bagaimana agent-mu beraksi</h2>"
        "<div class='card'>"
        "<p class='sub'>Wallet <b>controller agent</b> (yang terdaftar di ERC-8004) memanggil "
        "<span class='mono'>act(target, value, memo)</span>. Kontrak mengecek SEMUA rule on-chain — "
        "target ter-whitelist, ≤ max per aksi, ≤ cap harian, cooldown lewat, saldo &gt; halt floor. "
        "Aksi yang lolos otomatis jadi entry terverifikasi di Economic Memory dan naik ke Trust Score.</p>"
        "<pre class='code' id='snippet'></pre>"
        "<p class='sub'>Coba langsung (wallet yang connect harus = controller agent):</p>"
        "<div class='grid'>"
        "<div class='kv'><div class='k'>Target (ter-whitelist)</div><input id='aTgt' placeholder='0x…'></div>"
        "<div class='kv'><div class='k'>Value (BNB)</div><input id='aVal' value='0.001'></div>"
        "<div class='kv'><div class='k'>Memo</div><input id='aMemo' value='demo-trade'></div>"
        "</div><p><button onclick='doAct()'>agent.act()</button> <span id='aout' class='mono'></span></p></div>"
        f"{_SCRIPT.replace('__ADDR__', addr)}"
    )


_SCRIPT = """
<style>.code{background:#0a0e18;border:1px solid #1b2232;border-radius:10px;padding:14px;overflow-x:auto;
 font-family:ui-monospace,monospace;font-size:12.5px;color:#a5c0ff;white-space:pre;line-height:1.5}
select:focus{outline:none;border-color:#34d399}</style>
<script>
const VAULT='__ADDR__', RPC='%RPC%';
const S=%SEL%;
let ACC=null, OWNER=null;
const pad=(h)=>h.replace('0x','').padStart(64,'0');
const stripHex=(h)=>h.replace('0x','');
const weiWord=(bnb)=>pad((BigInt(Math.round(parseFloat(bnb||'0')*1e9))*1000000000n).toString(16));
const bnbWei=(bnb)=>'0x'+(BigInt(Math.round(parseFloat(bnb||'0')*1e9))*1000000000n).toString(16);
function fmtBnb(wei){ // BigInt wei -> string BNB (6 desimal)
  const neg=wei<0n; if(neg)wei=-wei; const s=wei.toString().padStart(19,'0');
  const i=s.slice(0,-18), f=s.slice(-18).slice(0,6).replace(/0+$/,'');
  return (neg?'-':'')+i+(f?'.'+f:'');}
async function rpc(method,params){
  const r=await fetch(RPC,{method:'POST',headers:{'content-type':'application/json'},
    body:JSON.stringify({jsonrpc:'2.0',id:1,method,params})});
  const j=await r.json(); if(j.error) throw new Error(j.error.message||JSON.stringify(j.error)); return j.result;}
const call=(data)=>rpc('eth_call',[{to:VAULT,data},'latest']);
const balOf=(a)=>rpc('eth_getBalance',[a,'latest']);

async function ensureChain(){
  await ethereum.request({method:'wallet_addEthereumChain',params:[{chainId:'0x61',chainName:'BSC Testnet',
    rpcUrls:['https://bsc-testnet.bnbchain.org'],nativeCurrency:{name:'tBNB',symbol:'tBNB',decimals:18},
    blockExplorerUrls:['https://testnet.bscscan.com']}]}).catch(()=>{});
  await ethereum.request({method:'wallet_switchEthereumChain',params:[{chainId:'0x61'}]});
  const [a]=await ethereum.request({method:'eth_requestAccounts'}); ACC=a; return a;}
async function connect(){
  try{ await ensureChain(); await refreshWho(); }
  catch(e){ document.getElementById('who').textContent='err: '+(e.message||e); }}
async function refreshWho(){
  const w=document.getElementById('who');
  if(!ACC){ w.textContent=''; return; }
  const isOwner = OWNER && ACC.toLowerCase()===OWNER.toLowerCase();
  w.innerHTML = ACC.slice(0,6)+'…'+ACC.slice(-4)+(isOwner?" <span class='badge b-ok'>owner ✓</span>":
    " <span class='badge b-dim'>bukan owner</span>");}
async function send(to,data,value){
  if(!ACC) await ensureChain();
  const p={from:ACC,to,data}; if(value) p.value=value;
  return ethereum.request({method:'eth_sendTransaction',params:[p]});}
function txlink(t){return 'tx: <a href="https://testnet.bscscan.com/tx/'+t+'">'+t.slice(0,18)+'…</a>';}

async function loadState(){
  const el=document.getElementById('state');
  try{
    const [ownerR,aidR,polR,spentR,winR,lastR,balR]=await Promise.all([
      call(S.owner),call(S.managerAgentId),call(S.policy),call(S.spentInWindow),
      call(S.windowStart),call(S.lastActionAt),balOf(VAULT)]);
    OWNER='0x'+stripHex(ownerR).slice(24);
    const aid=BigInt(aidR);
    const p=stripHex(polR); const w=(n)=>BigInt('0x'+p.slice(n*64,n*64+64));
    const maxTx=w(0),daily=w(1),cool=w(2),floor=w(3);
    const spent=BigInt(spentR), winStart=BigInt(winR), last=BigInt(lastR), bal=BigInt(balR);
    const now=BigInt(Math.floor(Date.now()/1000));
    const dayElapsed = now >= winStart + 86400n;
    const spentToday = dayElapsed ? 0n : spent;
    const cdLeft = last===0n?0n:(last+cool>now? last+cool-now : 0n);
    const headroom = bal>floor? bal-floor : 0n;
    const kv=(k,v)=>`<div class='kv'><div class='k'>${k}</div><div class='v'>${v}</div></div>`;
    el.innerHTML =
      kv('Balance', fmtBnb(bal)+' BNB') +
      kv('Manager agent', '#'+aid.toString()) +
      kv('Max per aksi', fmtBnb(maxTx)+' BNB') +
      kv('Cap harian', fmtBnb(daily)+' BNB') +
      kv('Terpakai hari ini', fmtBnb(spentToday)+' / '+fmtBnb(daily)+' BNB') +
      kv('Cooldown', cool.toString()+'s'+(cdLeft>0n?` <span class='badge b-warn'>sisa ${cdLeft}s</span>`:" <span class='badge b-ok'>siap</span>")) +
      kv('Halt floor', fmtBnb(floor)+' BNB') +
      kv('Headroom di atas floor', fmtBnb(headroom)+' BNB');
    // prefill policy editor + manager
    document.getElementById('pMax').value=fmtBnb(maxTx);
    document.getElementById('pDaily').value=fmtBnb(daily);
    document.getElementById('pCool').value=cool.toString();
    document.getElementById('pFloor').value=fmtBnb(floor);
    document.getElementById('mAid').value=aid.toString();
    await refreshWho();
  }catch(e){ el.innerHTML="<div class='kv'><div class='k'>Gagal baca chain</div><div class='v mono'>"+(e.message||e)+"</div></div>"; }}

async function deposit(){
  try{ const t=await send(VAULT,'0x',bnbWei(document.getElementById('depAmt').value));
    document.getElementById('fout').innerHTML=txlink(t); setTimeout(loadState,4000);
  }catch(e){document.getElementById('fout').textContent='err: '+(e.message||e)}}
async function doWithdraw(){
  try{ const t=await send(VAULT,S.withdraw+weiWord(document.getElementById('wAmt').value));
    document.getElementById('fout').innerHTML=txlink(t); setTimeout(loadState,4000);
  }catch(e){document.getElementById('fout').textContent='err: '+(e.message||e)}}
async function setTarget(){
  try{ const a=stripHex(document.getElementById('tgt').value.trim());
    const allow=document.getElementById('tgtAllow').value==='1'?'1':'0';
    const t=await send(VAULT,S.setTarget+pad(a)+pad(allow));
    document.getElementById('tout').innerHTML=txlink(t);
  }catch(e){document.getElementById('tout').textContent='err: '+(e.message||e)}}
async function setPolicy(){
  try{ const d=S.setPolicy+weiWord(document.getElementById('pMax').value)
      +weiWord(document.getElementById('pDaily').value)
      +pad(BigInt(document.getElementById('pCool').value||'0').toString(16))
      +weiWord(document.getElementById('pFloor').value);
    const t=await send(VAULT,d); document.getElementById('pout').innerHTML=txlink(t); setTimeout(loadState,4000);
  }catch(e){document.getElementById('pout').textContent='err: '+(e.message||e)}}
async function setManager(){
  try{ const t=await send(VAULT,S.setManager+pad(BigInt(document.getElementById('mAid').value).toString(16)));
    document.getElementById('mout').innerHTML=txlink(t); setTimeout(loadState,4000);
  }catch(e){document.getElementById('mout').textContent='err: '+(e.message||e)}}
function memoWord(s){let h='';for(const b of new TextEncoder().encode(s).slice(0,32))h+=b.toString(16).padStart(2,'0');return h.padEnd(64,'0');}
async function doAct(){
  try{ const tgt=stripHex(document.getElementById('aTgt').value.trim());
    const d=S.act+pad(tgt)+weiWord(document.getElementById('aVal').value)+memoWord(document.getElementById('aMemo').value);
    const t=await send(VAULT,d); document.getElementById('aout').innerHTML=txlink(t)+' — jadi track record terverifikasi';
    setTimeout(loadState,4000);
  }catch(e){document.getElementById('aout').textContent='err: '+(e.message||e)}}

document.getElementById('snippet').textContent =
`// agent controller memanggil vault (ethers v6)
const vault = new ethers.Contract("${VAULT}",
  ["function act(address target,uint256 value,bytes32 memo)"],
  agentControllerSigner);            // wallet terdaftar di ERC-8004
const memo = ethers.encodeBytes32String("trade-001");
await vault.act(TARGET, ethers.parseEther("0.001"), memo);
// lolos policy -> otomatis tercatat di Verdix Economic Memory`;

if(window.ethereum){ ethereum.on&&ethereum.on('accountsChanged',(a)=>{ACC=a[0]||null;refreshWho();}); }
loadState();
</script>
""".replace("%RPC%", RPC).replace("%SEL%", str(SEL).replace("'", '"'))


def vault_page(page_fn, addr: str) -> str:
    return page_fn(f"Vault {addr[:10]}… — Verdix", _body(addr))
