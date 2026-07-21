# Verdix x402 — pay-per-call trust data untuk AI agent

Layer monetisasi di atas Verdix Reputation API via protokol [x402](https://x402.org):
caller (agent/manusia) bayar USDC per-request, tanpa akun/API key. Servis otomatis
discoverable oleh agent lain via x402 Bazaar.

**Publik:** `https://verdix-api.kilatlab.com/x402/` (katalog, gratis)

## Servis berbayar (8)

| Endpoint | Harga | Isi |
|---|---|---|
| `GET /x402/agents` | $0.002 | Semua agent Verdix-native + Trust Score live |
| `GET /x402/agent/:id` | $0.005 | Rincian skor lengkap satu agent |
| `GET /x402/agent/:id/cv` | $0.005 | Economic CV (markdown) |
| `GET /x402/entries` | $0.002 | Entry Economic Memory terbaru |
| `GET /x402/bitagent` | $0.005 | Leaderboard ekosistem BitAgent (60+ agent) |
| `GET /x402/bitagent/:handle` | $0.005 | Detail skor + cek identity ERC-8004 |
| `GET /x402/memory/:hash` | $0.003 | Payload terverifikasi di balik dataHash |
| `GET /x402/dossier/:id` | $0.02 | **Premium**: profil + komponen + memory + CV sekali call |

Gratis: `GET /x402/` (katalog) dan `GET /x402/health`.

## Arsitektur

```
caller → nginx (/x402/) → node :8402 (index.js, @x402/express) → Verdix API :8600
                                └─ facilitator (verify+settle USDC)
```

- systemd: `verdix-x402` (env di `/root/.verdix-keys/x402.env`)
- Wallet penerima: Coinbase Agentic Wallet (`awal`), companion Electron jalan
  headless via systemd `awal-wallet` (Xvfb).

## Aktivasi (sekali, setelah sign-in awal)

```bash
npx awal auth login <email>   # OTP ke email
npx awal auth verify <otp>
bash /root/verdix/x402/activate.sh   # isi PAY_TO + restart, verifikasi 402
```

## Testnet → Mainnet

Default sekarang **Base Sepolia** (`eip155:84532`) karena facilitator publik
x402.org belum support Base mainnet. Buat terima USDC beneran:
1. Bikin CDP API key di portal Coinbase Developer Platform
2. Isi di `/root/.verdix-keys/x402.env`:
   `X402_NETWORK=eip155:8453` + `X402_FACILITATOR=<url facilitator CDP>` (+ kredensial sesuai SDK CDP)
3. `systemctl restart verdix-x402`

## Cara caller bayar (contoh agent lain)

```bash
npx awal x402 details https://verdix-api.kilatlab.com/x402/agent/1
npx awal x402 pay     https://verdix-api.kilatlab.com/x402/agent/1
```
