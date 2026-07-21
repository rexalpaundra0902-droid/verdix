# Verdix — Mainnet Readiness Checklist

Status: **BELUM SIAP mainnet** (2026-07-21). Testnet solid; mainnet butuh item di
bawah + yang terpenting: **demand nyata (operator eksternal)**. Mainnet = kontrak
immutable + dana user; bug tak bisa di-patch. Jangan buru-buru.

Legenda: `[R]` = butuh Reku / eksternal · `[C]` = Claude bisa bantu/kerjain · `[$]` = keluar biaya.

---

## GATE 0 — Prasyarat bisnis (INI yang menentukan, bukan teknis)
- [ ] `[R]` **3-5 operator eksternal pakai di testnet** → economic memory NYATA (non-self).
      Mainnet dgn 2 agent internal = nol beda cerita. Ini jalur kritis, dulukan.
- [ ] `[R]` Data operator eksternal jadi dasar keputusan mainnet + proposal grant.
- [ ] `[R]` Budget audit eksternal siap (~$5-30k tergantung firma).

## GATE 1 — Keamanan (WAJIB sebelum dana nyata)
- [ ] `[R][$]` **Audit eksternal profesional** (Cyfrin / Code4rena / Sherlock).
      Audit internal (multi-agent+Slither, docs/AUDIT + REAUDIT) = perlu tapi TIDAK cukup utk mainnet.
- [ ] `[R]` **Multisig (Gnosis Safe) + timelock** jadi owner: EconomicMemory, StressOracle,
      TaskEscrow, VaultFactory. Sekarang single EOA `0xeB51…` = titik kegagalan tunggal (HIGH-2).
- [ ] `[R]` **Hardware wallet** (Ledger) utk deploy + owner key. HARAM plaintext di VPS
      (`/root/.verdix-keys/*.key` cuma utk testnet).
- [ ] `[R/C]` **Keputusan wash-trading residual**: level sekarang (blok 1-EOA) cukup, atau
      butuh stake-gated settlement / counterparty-consent redesign? Reputasi yang bisa
      di-game = value prop runtuh. `[C]` bisa implement redesign kalau diputuskan.
- [ ] `[C]` **Emergency pause / circuit breaker** global di kontrak value-moving (belum ada).
- [ ] `[C]` gitleaks + pastikan nol secret ke-commit; `.env`/keystore tak pernah tracked.

## GATE 2 — Arsitektur & tokenomics
- [ ] `[C]` **Re-arsitektur storage EconomicMemory** ke event + merkle/indexer.
      Sekarang simpan entry PENUH on-chain — murah di testnet, MAHAL di mainnet BSC.
      (Design note v9 sudah antisipasi ini utk produksi.)
- [ ] `[R]` **Keputusan tokenomics VDX**: TGE atau utility-only? (memory: TGE ditunda sampai
      usage nyata). Ada implikasi regulasi (token + pegang dana user).
- [ ] `[R]` **Cek regulasi/legal** jurisdiksi (handling dana user + token).

## GATE 3 — Deploy mekanik (relatif gampang, terakhir)
- [ ] `[R][$]` BNB mainnet utk gas (deploy 9 kontrak + wiring).
- [ ] `[R]` RPC mainnet reliable (endpoint berbayar, bukan publik load-balanced).
- [ ] `[C]` Chain config 56 (mainnet) di semua: frontend, verdix-api, deployments, script.
- [ ] `[C]` Deploy via keystore/hardware (bukan `--private-key` plaintext) + simulasi sebelum broadcast.
- [ ] `[C]` Re-verify 9 kontrak di BscScan mainnet (etherscan key jalan utk mainnet).
- [ ] `[C]` Update semua rujukan alamat → alamat mainnet (pola sama redeploy testnet).
- [ ] `[R][$]` **Custom domain** (verdix.xyz dsb) — `.pages.dev` keliatan proyek weekend
      di mata juri/VC (WEB_AUDIT_2026-07-21).

## GATE 4 — Pasca-deploy
- [ ] `[C]` Monitoring on-chain (event listener anomali) + alert.
- [ ] `[C]` Runbook incident + prosedur pause via multisig.
- [ ] `[R]` Backup baseline + dokumentasi alamat mainnet di tempat aman.

---

## Rekomendasi urutan
1. **Sekarang:** GATE 0 (beta operator) — jangan sentuh mainnet dulu.
2. Setelah ada demand: GATE 1 (audit eksternal + multisig + hardware key).
3. Paralel: GATE 2 (re-arsitektur storage, keputusan token).
4. Terakhir & tercepat: GATE 3 (deploy) + GATE 4 (monitor).

Estimasi jujur: mainnet realistis **berbulan-bulan** lagi, di-gate audit eksternal +
adopsi — bukan pekerjaan seminggu. Testnet sekarang sudah cukup buat menarik operator.
