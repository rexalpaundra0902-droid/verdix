#!/usr/bin/env python3
"""Verdix Trust Directory — halaman web publik (server-side render, tanpa dependency).

Dipakai api/server.py:
  GET /web                → leaderboard: agent Verdix + seluruh agent BitAgent chain 97
  GET /web/agent/<id>     → profil agent Verdix (on-chain economic memory)
  GET /web/bitagent/<h>   → profil agent BitAgent (platform stats + cek identity on-chain)
"""

from __future__ import annotations

import html
import json as _json

# ── i18n web app: key EN (collapsed whitespace) → [id, zh, ja, ko, es, ru] ──
# Pilihan bahasa share localStorage 'vdx-lang' dgn landing.
I18N = {
 "Directory": ["Direktori","目录","ディレクトリ","디렉터리","Directorio","Каталог"],
 "Launch App": ["Buka App","启动应用","アプリを開く","앱 실행","Abrir app","Открыть приложение"],
 "Verdix Trust Directory": ["Direktori Trust Verdix","Verdix 信任目录","Verdix トラストディレクトリ","Verdix 트러스트 디렉터리","Directorio de confianza Verdix","Каталог доверия Verdix"],
 "Trust scores for AI agents — computed from proofs, not claims. On-chain economic memory (BSC testnet) + verified payloads on Membase.":
   ["Skor kepercayaan AI agent — dihitung dari bukti, bukan klaim. Economic memory on-chain (BSC testnet) + payload terverifikasi di Membase.",
    "AI 代理的信任评分 — 基于证明计算，而非声明。链上经济记忆（BSC 测试网）+ Membase 上的已验证数据。",
    "AIエージェントの信頼スコア — 主張ではなく証明から算出。オンチェーン経済メモリ（BSCテストネット）+ Membase上の検証済みペイロード。",
    "AI 에이전트 신뢰 점수 — 주장이 아닌 증명으로 계산. 온체인 경제 기억(BSC 테스트넷) + Membase의 검증된 페이로드.",
    "Puntuaciones de confianza para agentes de IA: calculadas a partir de pruebas, no de afirmaciones. Memoria económica on-chain (BSC testnet) + payloads verificados en Membase.",
    "Рейтинги доверия ИИ-агентов — на основе доказательств, а не заявлений. Ончейн-память (тестнет BSC) + проверенные данные в Membase."],
 "→ Create your Verified Agent Vault": ["→ Buat Verified Agent Vault-mu","→ 创建你的验证代理金库","→ 検証済みエージェントボールトを作成","→ 검증된 에이전트 볼트 만들기","→ Crea tu bóveda de agente verificada","→ Создайте своё верифицированное хранилище"],
 "Verdix-native agents (full on-chain economic memory)": ["Agent Verdix-native (economic memory on-chain penuh)","Verdix 原生代理（完整链上经济记忆）","Verdixネイティブエージェント（完全オンチェーン経済メモリ）","Verdix 네이티브 에이전트(완전한 온체인 경제 기억)","Agentes nativos de Verdix (memoria económica on-chain completa)","Verdix-native агенты (полная ончейн-память)"],
 "Agent": ["Agent","代理","エージェント","에이전트","Agente","Агент"],
 "History": ["Riwayat","历史","履歴","이력","Historial","История"],
 "Skin in the game": ["Skin in the game","质押投入","ステーク量","스테이크","Compromiso propio","Собственная ставка"],
 "founding operator": ["founding operator","创始运营者","ファウンディングオペレーター","파운딩 오퍼레이터","operador fundador","оператор-основатель"],
 "★ founding operator — permanent, original registry slot": ["★ founding operator — permanen, slot awal registry","★ 创始运营者 — 永久，注册表初始席位","★ ファウンディングオペレーター — 恒久、レジストリ初期スロット","★ 파운딩 오퍼레이터 — 영구, 레지스트리 초기 슬롯","★ operador fundador — permanente, slot original del registro","★ оператор-основатель — навсегда, изначальный слот реестра"],
 "Jobs": ["Job","任务","ジョブ","작업","Trabajos","Задачи"],
 "Revenue": ["Pendapatan","收入","収益","수익","Ingresos","Доход"],
 "Identity ERC-8004 · economic memory on-chain · payloads on Membase": ["Identitas ERC-8004 · economic memory on-chain · payload di Membase","ERC-8004 身份 · 链上经济记忆 · Membase 数据","ERC-8004 ID · オンチェーン経済メモリ · Membaseペイロード","ERC-8004 신원 · 온체인 경제 기억 · Membase 페이로드","Identidad ERC-8004 · memoria económica on-chain · payloads en Membase","Идентичность ERC-8004 · ончейн-память · данные в Membase"],
 "Verified actions": ["Aksi terverifikasi","已验证操作","検証済みアクション","검증된 액션","Acciones verificadas","Проверенные действия"],
 "VDX staked": ["VDX di-stake","已质押 VDX","VDXステーク","VDX 스테이킹","VDX en stake","VDX в стейке"],
 "Disputes lost": ["Kalah dispute","败诉争议","敗訴した紛争","패소한 분쟁","Disputas perdidas","Проигранные споры"],
 "Control changes": ["Perpindahan kontrol","控制权变更","コントロール変更","컨트롤 변경","Cambios de control","Смены контроля"],
 "Score components": ["Komponen skor","评分组件","スコア構成要素","점수 구성요소","Componentes de la puntuación","Компоненты рейтинга"],
 "success rate": ["success rate","成功率","成功率","성공률","tasa de éxito","доля успеха"],
 "economic volume": ["volume ekonomi","经济量","経済ボリューム","경제 볼륨","volumen económico","экономический объём"],
 "counterparty diversity": ["diversitas counterparty","交易对手多样性","カウンターパーティ多様性","상대방 다양성","diversidad de contrapartes","разнообразие контрагентов"],
 "stress behavior": ["perilaku saat stress","压力行为","ストレス時挙動","스트레스 행동","comportamiento bajo estrés","поведение в стрессе"],
 "dispute record": ["rekor dispute","争议记录","紛争記録","분쟁 기록","historial de disputas","история споров"],
 "Economic memory (last 15)": ["Economic memory (15 terakhir)","经济记忆（最近 15 条）","経済メモリ（直近15件）","경제 기억(최근 15개)","Memoria económica (últimas 15)","Экономическая память (последние 15)"],
 "Entry": ["Entry","条目","エントリ","엔트리","Entrada","Запись"],
 "Outcome": ["Hasil","结果","結果","결과","Resultado","Исход"],
 "Payload (verify)": ["Payload (verifikasi)","数据（验证）","ペイロード（検証）","페이로드(검증)","Payload (verificar)","Данные (проверка)"],
 "Verify it yourself:": ["Verifikasi sendiri:","自己验证：","自分で検証：","직접 검증:","Verifícalo tú mismo:","Проверьте сами:"],
 "← directory": ["← direktori","← 目录","← ディレクトリ","← 디렉터리","← directorio","← каталог"],
 "+ create another": ["+ buat lagi","+ 再创建一个","+ もう1つ作成","+ 하나 더 만들기","+ crear otra","+ создать ещё"],
 "identity verified on-chain ✓": ["identity terverifikasi on-chain ✓","身份已链上验证 ✓","ID オンチェーン検証済み ✓","신원 온체인 검증됨 ✓","identidad verificada on-chain ✓","идентичность подтверждена ончейн ✓"],
 "identity not yet verified on-chain": ["identity belum terverifikasi on-chain","身份尚未链上验证","IDは未検証","신원 미검증","identidad aún no verificada on-chain","идентичность ещё не подтверждена"],
 "Status": ["Status","状态","ステータス","상태","Estado","Статус"],
 "Create Your Verified Agent Vault": ["Buat Verified Agent Vault-mu","创建你的验证代理金库","検証済みエージェントボールトを作成","검증된 에이전트 볼트 만들기","Crea tu bóveda de agente verificada","Создайте верифицированное хранилище агента"],
 "Your own non-custodial vault: your AI agent can trade, but can never break policy — and every action becomes a verifiable on-chain track record. BSC Testnet (chain 97).":
   ["Vault non-custodial milikmu sendiri: AI agent-mu bisa trading, tapi gak akan pernah bisa melanggar policy — dan tiap aksinya jadi track record on-chain terverifikasi. BSC Testnet (chain 97).",
    "你自己的非托管金库：你的 AI 代理可以交易，但永远无法违反策略 — 每个操作都成为可验证的链上业绩记录。BSC 测试网（chain 97）。",
    "あなた自身のノンカストディアルボールト：AIエージェントは取引できるが、ポリシーは決して破れない — すべてのアクションが検証可能なオンチェーン実績になる。BSCテストネット（chain 97）。",
    "당신만의 논커스터디얼 볼트: AI 에이전트는 거래할 수 있지만 정책은 절대 어길 수 없습니다 — 모든 행동이 검증 가능한 온체인 실적이 됩니다. BSC 테스트넷(chain 97).",
    "Tu propia bóveda no custodial: tu agente de IA puede operar, pero nunca romper la política — y cada acción se convierte en un historial on-chain verificable. BSC Testnet (chain 97).",
    "Ваше некастодиальное хранилище: ИИ-агент может торговать, но не может нарушить политику — каждое действие становится проверяемым ончейн-послужным списком. BSC Testnet (chain 97)."],
 "Step 1 — Register agent (ERC-8004)": ["Step 1 — Daftarkan agent (ERC-8004)","第 1 步 — 注册代理（ERC-8004）","ステップ1 — エージェント登録（ERC-8004）","1단계 — 에이전트 등록(ERC-8004)","Paso 1 — Registra el agente (ERC-8004)","Шаг 1 — Зарегистрируйте агента (ERC-8004)"],
 "Once per agent. The registering wallet becomes the agent's controller.": ["Sekali per agent. Wallet yang mendaftar jadi controller agent.","每个代理一次。注册钱包成为代理的控制者。","エージェントごとに1回。登録したウォレットがコントローラーになる。","에이전트당 한 번. 등록한 지갑이 컨트롤러가 됩니다.","Una vez por agente. La wallet que registra se convierte en el controlador.","Один раз на агента. Кошелёк регистрации становится контроллером."],
 "Register Agent": ["Daftarkan Agent","注册代理","エージェント登録","에이전트 등록","Registrar agente","Зарегистрировать агента"],
 "Step 2 — Create vault + policy": ["Step 2 — Buat vault + policy","第 2 步 — 创建金库 + 策略","ステップ2 — ボールト作成 + ポリシー","2단계 — 볼트 생성 + 정책","Paso 2 — Crea la bóveda + política","Шаг 2 — Создайте хранилище + политику"],
 "Max per action (BNB)": ["Max per aksi (BNB)","单笔上限（BNB）","1アクション上限（BNB）","액션당 최대(BNB)","Máx. por acción (BNB)","Макс. на действие (BNB)"],
 "Daily cap (BNB)": ["Cap harian (BNB)","每日上限（BNB）","1日上限（BNB）","일일 한도(BNB)","Tope diario (BNB)","Дневной лимит (BNB)"],
 "Cooldown (seconds)": ["Cooldown (detik)","冷却（秒）","クールダウン（秒）","쿨다운(초)","Enfriamiento (segundos)","Пауза (секунды)"],
 "Halt floor (BNB)": ["Halt floor (BNB)","止损底线（BNB）","ホルトフロア（BNB）","홀트 플로어(BNB)","Suelo de parada (BNB)","Нижний порог (BNB)"],
 "Initial deposit (BNB)": ["Deposit awal (BNB)","初始存款（BNB）","初回デポジット（BNB）","초기 예치금(BNB)","Depósito inicial (BNB)","Начальный депозит (BNB)"],
 "Create Vault": ["Buat Vault","创建金库","ボールト作成","볼트 만들기","Crear bóveda","Создать хранилище"],
 "Already have a vault?": ["Sudah punya vault?","已经有金库？","既にボールトをお持ち？","이미 볼트가 있나요?","¿Ya tienes una bóveda?","Уже есть хранилище?"],
 "Enter your wallet address to find every vault you've created.": ["Masukkan alamat wallet buat menemukan semua vault yang pernah kamu buat.","输入你的钱包地址，找回你创建过的所有金库。","ウォレットアドレスを入力して、作成した全ボールトを検索。","지갑 주소를 입력해 만든 모든 볼트를 찾으세요.","Introduce tu dirección de wallet para encontrar todas tus bóvedas.","Введите адрес кошелька, чтобы найти все свои хранилища."],
 "Find my vaults": ["Cari vault-ku","查找我的金库","マイボールト検索","내 볼트 찾기","Buscar mis bóvedas","Найти мои хранилища"],
 "Step 3 — Manage & use": ["Step 3 — Kelola & pakai","第 3 步 — 管理与使用","ステップ3 — 管理と利用","3단계 — 관리 & 사용","Paso 3 — Gestiona y usa","Шаг 3 — Управляйте и используйте"],
 "Once the vault is live, manage everything from the browser (deposit, venue whitelist, withdraw, policy) — no BscScan digging. Your agent calls":
   ["Begitu vault jadi, kelola semuanya dari browser (deposit, whitelist venue, withdraw, policy) — tanpa gali BscScan. Agent-mu memanggil",
    "金库上线后，全部在浏览器中管理（存款、白名单、提款、策略）— 无需翻 BscScan。你的代理调用",
    "ボールトが動き出したら、すべてブラウザで管理（入金・ホワイトリスト・出金・ポリシー）— BscScan漁り不要。エージェントが呼ぶのは",
    "볼트가 가동되면 브라우저에서 모두 관리하세요(예치, 화이트리스트, 출금, 정책) — BscScan 뒤질 필요 없음. 에이전트가 호출:",
    "Con la bóveda activa, gestiona todo desde el navegador (depósitos, lista blanca, retiros, política), sin excavar en BscScan. Tu agente llama a",
    "Когда хранилище запущено, управляйте всем из браузера (депозит, белый список, вывод, политика) — без раскопок в BscScan. Агент вызывает"],
 "; every policy-compliant action automatically becomes a verified track record on your agent's public profile.":
   ["; tiap aksi patuh policy otomatis jadi track record terverifikasi di profil publik agent-mu.",
    "；每个合规操作都会自动成为代理公开档案中的已验证记录。",
    "；ポリシー準拠のアクションはすべて自動で公開プロフィールの検証済み実績になる。",
    "; 정책을 준수한 모든 액션은 자동으로 공개 프로필의 검증된 실적이 됩니다.",
    "; cada acción conforme se convierte automáticamente en historial verificado en el perfil público.",
    "; каждое соответствующее действие автоматически становится проверенной записью в публичном профиле."],
 "Manage Vault": ["Kelola Vault","管理金库","ボールト管理","볼트 관리","Gestionar bóveda","Управление хранилищем"],
 "Your non-custodial vault on BSC Testnet. State is read straight from the chain — the controls below enforce on-chain policy; your agent can never break it.":
   ["Vault non-custodial-mu di BSC Testnet. State dibaca langsung dari chain — kontrol di bawah menegakkan policy on-chain; agent-mu gak akan pernah bisa melanggarnya.",
    "你在 BSC 测试网的非托管金库。状态直接从链上读取 — 下方控制执行链上策略；你的代理永远无法违反。",
    "BSCテストネット上のノンカストディアルボールト。状態はチェーンから直接読取 — 下のコントロールがオンチェーンポリシーを強制。エージェントは決して破れない。",
    "BSC 테스트넷의 논커스터디얼 볼트. 상태는 체인에서 직접 읽습니다 — 아래 컨트롤이 온체인 정책을 강제하며 에이전트는 절대 어길 수 없습니다.",
    "Tu bóveda no custodial en BSC Testnet. El estado se lee directo de la cadena; los controles de abajo aplican la política on-chain y tu agente nunca puede romperla.",
    "Ваше некастодиальное хранилище в тестнете BSC. Состояние читается прямо из блокчейна — контролы ниже применяют ончейн-политику; агент не может её нарушить."],
 "No wallet extension?": ["Gak punya wallet extension?","没有钱包插件？","ウォレット拡張なし？","지갑 확장 프로그램이 없나요?","¿Sin extensión de wallet?","Нет расширения кошелька?"],
 "Connect with WalletConnect (QR) →": ["Hubungkan via WalletConnect (QR) →","用 WalletConnect 连接（扫码）→","WalletConnectで接続（QR）→","WalletConnect로 연결(QR) →","Conectar con WalletConnect (QR) →","Подключить через WalletConnect (QR) →"],
 "Connect wallet": ["Hubungkan wallet","连接钱包","ウォレット接続","지갑 연결","Conectar wallet","Подключить кошелёк"],
 "Live state": ["State live","实时状态","ライブ状態","실시간 상태","Estado en vivo","Живое состояние"],
 "Loading…": ["Memuat…","加载中…","読み込み中…","로딩 중…","Cargando…","Загрузка…"],
 "↻ Refresh": ["↻ Segarkan","↻ 刷新","↻ 更新","↻ 새로고침","↻ Actualizar","↻ Обновить"],
 "Owner controls": ["Kontrol owner","所有者控制","オーナーコントロール","소유자 컨트롤","Controles del propietario","Управление владельца"],
 "Only the vault owner can use these controls (the contract rejects anyone else).": ["Hanya owner vault yang bisa pakai kontrol ini (kontrak menolak yang lain).","只有金库所有者能使用这些控制（合约拒绝其他人）。","これらのコントロールはボールトオーナーのみ使用可（コントラクトが他を拒否）。","볼트 소유자만 이 컨트롤을 사용할 수 있습니다(컨트랙트가 다른 사람을 거부).","Solo el propietario de la bóveda puede usar estos controles (el contrato rechaza al resto).","Только владелец хранилища может использовать эти контролы (контракт отклонит остальных)."],
 "Deposit / Withdraw (BNB)": ["Deposit / Withdraw (BNB)","存款 / 提款（BNB）","入金 / 出金（BNB）","예치 / 출금(BNB)","Depósito / Retiro (BNB)","Депозит / Вывод (BNB)"],
 "Deposit": ["Deposit","存款","入金","예치","Depositar","Депозит"],
 "Withdraw": ["Withdraw","提款","出金","출금","Retirar","Вывести"],
 "Whitelist venue (setTarget)": ["Whitelist venue (setTarget)","白名单地址（setTarget）","ホワイトリスト（setTarget）","화이트리스트(setTarget)","Lista blanca (setTarget)","Белый список (setTarget)"],
 "The agent may only send funds to whitelisted addresses. Add legitimate destinations (e.g. a venue router) before the agent acts.":
   ["Agent cuma boleh kirim dana ke alamat yang di-whitelist. Tambah tujuan sah (mis. router venue) sebelum agent beraksi.",
    "代理只能向白名单地址转账。在代理行动前添加合法目标（如交易路由）。",
    "エージェントはホワイトリストのアドレスにのみ送金可。行動前に正当な宛先（例：ルーター）を追加。",
    "에이전트는 화이트리스트 주소로만 자금을 보낼 수 있습니다. 행동 전에 정당한 대상을 추가하세요.",
    "El agente solo puede enviar fondos a direcciones en lista blanca. Añade destinos legítimos antes de que actúe.",
    "Агент может отправлять средства только на адреса из белого списка. Добавьте легитимные адреса до его действий."],
 "Target address": ["Alamat target","目标地址","ターゲットアドレス","대상 주소","Dirección objetivo","Целевой адрес"],
 "Allow?": ["Izinkan?","允许？","許可？","허용?","¿Permitir?","Разрешить?"],
 "Set target": ["Set target","设置目标","ターゲット設定","타깃 설정","Fijar objetivo","Задать адрес"],
 "Update policy": ["Update policy","更新策略","ポリシー更新","정책 업데이트","Actualizar política","Обновить политику"],
 "Set policy": ["Set policy","设置策略","ポリシー設定","정책 설정","Fijar política","Задать политику"],
 "Change manager agent (setManager)": ["Ganti manager agent (setManager)","更换管理代理（setManager）","マネージャー変更（setManager）","매니저 에이전트 변경(setManager)","Cambiar agente gestor (setManager)","Сменить агента-менеджера (setManager)"],
 "Set manager": ["Set manager","设置管理者","マネージャー設定","매니저 설정","Fijar gestor","Задать менеджера"],
 "How your agent acts": ["Cara agent-mu beraksi","你的代理如何行动","エージェントの動き方","에이전트가 행동하는 방법","Cómo actúa tu agente","Как действует ваш агент"],
 "The agent's": ["Wallet","代理的","エージェントの","에이전트의","La","У агента"],
 "controller wallet": ["controller agent","控制者钱包","コントローラーウォレット","컨트롤러 지갑","wallet controladora","кошелёк-контроллер"],
 "(registered via ERC-8004) calls": ["(terdaftar via ERC-8004) memanggil","（通过 ERC-8004 注册）调用","（ERC-8004で登録済み）が呼ぶのは","(ERC-8004로 등록됨)이 호출:","(registrada vía ERC-8004) llama a","(зарегистрированный через ERC-8004) вызывает"],
 ". The contract checks EVERY rule on-chain — whitelisted target, ≤ max per action, ≤ daily cap, cooldown elapsed, balance > halt floor. Compliant actions automatically become verified Economic Memory entries and feed the Trust Score.":
   [". Kontrak mengecek SEMUA rule on-chain — target ter-whitelist, ≤ max per aksi, ≤ cap harian, cooldown lewat, saldo > halt floor. Aksi patuh otomatis jadi entry Economic Memory terverifikasi dan masuk Trust Score.",
    "。合约在链上检查每一条规则 — 白名单目标、≤单笔上限、≤每日上限、冷却已过、余额 > 止损底线。合规操作自动成为已验证的 Economic Memory 条目并计入 Trust Score。",
    "。コントラクトが全ルールをオンチェーンで検査 — ホワイトリスト、≤上限、≤日次上限、クールダウン経過、残高>フロア。準拠アクションは自動で検証済みEconomic Memoryエントリになり、Trust Scoreに反映。",
    "。컨트랙트가 모든 규칙을 온체인에서 검사합니다 — 화이트리스트, ≤ 액션당 최대, ≤ 일일 한도, 쿨다운 경과, 잔고 > 홀트 플로어. 준수 액션은 자동으로 검증된 Economic Memory 엔트리가 되어 Trust Score에 반영됩니다.",
    ". El contrato comprueba TODAS las reglas on-chain: objetivo en lista blanca, ≤ máx. por acción, ≤ tope diario, enfriamiento cumplido, saldo > suelo. Las acciones conformes se vuelven entradas verificadas de Economic Memory y alimentan el Trust Score.",
    ". Контракт проверяет ВСЕ правила ончейн — белый список, ≤ лимита на действие, ≤ дневного лимита, пауза прошла, баланс > порога. Соответствующие действия автоматически становятся записями Economic Memory и влияют на Trust Score."],
 "Try it live (connected wallet must be the agent controller):": ["Coba langsung (wallet yang connect harus controller agent):","现场试试（连接的钱包必须是代理控制者）：","ライブで試す（接続ウォレット＝コントローラー必須）：","라이브로 시도(연결된 지갑이 컨트롤러여야 함):","Pruébalo en vivo (la wallet conectada debe ser el controlador):","Попробуйте вживую (подключённый кошелёк должен быть контроллером):"],
 "Target (whitelisted)": ["Target (ter-whitelist)","目标（白名单内）","ターゲット（WL内）","대상(화이트리스트)","Objetivo (en lista blanca)","Цель (из белого списка)"],
 "Value (BNB)": ["Nilai (BNB)","金额（BNB）","金額（BNB）","금액(BNB)","Valor (BNB)","Сумма (BNB)"],
 "Balance": ["Saldo","余额","残高","잔고","Saldo","Баланс"],
 "Manager agent": ["Manager agent","管理代理","マネージャー","매니저 에이전트","Agente gestor","Агент-менеджер"],
 "Max per action": ["Max per aksi","单笔上限","1アクション上限","액션당 최대","Máx. por acción","Макс. на действие"],
 "Daily cap": ["Cap harian","每日上限","日次上限","일일 한도","Tope diario","Дневной лимит"],
 "Spent today": ["Terpakai hari ini","今日已用","本日消費","오늘 지출","Gastado hoy","Потрачено сегодня"],
 "ready": ["siap","就绪","準備OK","준비됨","listo","готово"],
 "Halt floor": ["Halt floor","止损底线","ホルトフロア","홀트 플로어","Suelo de parada","Нижний порог"],
 "Headroom above floor": ["Ruang di atas floor","底线上余量","フロア上の余裕","플로어 위 여유","Margen sobre el suelo","Запас над порогом"],
 "not owner": ["bukan owner","非所有者","オーナーではない","소유자 아님","no propietario","не владелец"],
 "Failed to read chain": ["Gagal baca chain","读取链失败","チェーン読取失敗","체인 읽기 실패","Error al leer la cadena","Не удалось прочитать блокчейн"],
 "Agent not found": ["Agent tidak ditemukan","未找到代理","エージェントが見つかりません","에이전트를 찾을 수 없음","Agente no encontrado","Агент не найден"],
 "Verdix — verifiable economic memory for AI agents · live data from BSC testnet & Membase ·":
   ["Verdix — economic memory terverifikasi untuk AI agent · data live dari BSC testnet & Membase ·",
    "Verdix — AI 代理的可验证经济记忆 · 来自 BSC 测试网与 Membase 的实时数据 ·",
    "Verdix — AIエージェントの検証可能な経済メモリ · BSCテストネット&Membaseのライブデータ ·",
    "Verdix — AI 에이전트의 검증 가능한 경제 기억 · BSC 테스트넷 & Membase 라이브 데이터 ·",
    "Verdix: memoria económica verificable para agentes de IA · datos en vivo de BSC testnet y Membase ·",
    "Verdix — проверяемая экономическая память для ИИ-агентов · живые данные из тестнета BSC и Membase ·"],
 "source": ["sumber","源码","ソース","소스","código","исходники"],
 "· testnet only, not investment advice": ["· testnet saja, bukan saran investasi","· 仅测试网，非投资建议","· テストネットのみ、投資助言ではない","· 테스트넷 전용, 투자 조언 아님","· solo testnet, no es consejo de inversión","· только тестнет, не инвестиционный совет"],
}
_LANGS = ["id", "zh", "ja", "ko", "es", "ru"]
_DICTS_JSON = _json.dumps({lang: {k: v[i] for k, v in I18N.items()} for i, lang in enumerate(_LANGS)},
                          ensure_ascii=False, separators=(",", ":"))

LANG_SEL = ("<select id='langSel' class='lang-sel' aria-label='Language'>"
            "<option value='en'>EN</option><option value='id'>ID</option>"
            "<option value='zh'>中文</option><option value='ja'>日本語</option>"
            "<option value='ko'>한국어</option><option value='es'>ES</option>"
            "<option value='ru'>RU</option></select>")

I18N_SCRIPT = r"""<script>
(function(){
var DICTS=%DICTS%;
var cur=localStorage.getItem('vdx-lang')||'en';
if(cur!=='en'&&!DICTS[cur])cur='en';
function norm(s){return s.replace(/[\u2019\u2018]/g,"'").replace(/\s+/g,' ').trim();}
function apply(lang){
  var w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,null),n,
      d=(lang==='en')?null:DICTS[lang];
  while((n=w.nextNode())){
    var orig=n._o||(n._o=n.textContent);
    var k=norm(orig); if(!k)continue;
    if(d&&d[k])n.textContent=d[k];
    else if(n.textContent!==orig)n.textContent=orig;
  }
  document.documentElement.setAttribute('lang',lang);
  localStorage.setItem('vdx-lang',lang);cur=lang;
  var s=document.getElementById('langSel');if(s&&s.value!==lang)s.value=lang;
}
window.__vdxI18nApply=function(){apply(cur);};
var s=document.getElementById('langSel');
if(s){s.value=cur;s.addEventListener('change',function(){apply(s.value);});}
if(cur!=='en')apply(cur);
})();
</script>""".replace("%DICTS%", _DICTS_JSON)

CSS = """
:root{color-scheme:dark}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#07090f;color:#e8ecf4;font:15px/1.65 system-ui,-apple-system,sans-serif;padding:28px 20px;max-width:1000px;margin:0 auto;position:relative}
body::before{content:'';position:fixed;inset:0;z-index:-1;background:
 radial-gradient(600px 400px at 85% -10%,rgba(139,92,246,.16),transparent 60%),
 radial-gradient(700px 500px at -10% 20%,rgba(52,211,153,.10),transparent 60%),
 linear-gradient(rgba(122,162,255,.035) 1px,transparent 1px),
 linear-gradient(90deg,rgba(122,162,255,.035) 1px,transparent 1px);
 background-size:auto,auto,44px 44px,44px 44px}
a{color:#7aa2ff;text-decoration:none;transition:.2s}a:hover{color:#a5c0ff}
h1{font-size:clamp(24px,4vw,32px);font-weight:800;margin-bottom:4px;
 background:linear-gradient(90deg,#e8ecf4,#34d399 55%,#7aa2ff);-webkit-background-clip:text;background-clip:text;color:transparent}
h2{font-size:18px;margin:26px 0 10px;color:#cdd6e4}
.sub{color:#8b93a7;margin-bottom:20px}
.badge{display:inline-block;padding:3px 12px;border-radius:99px;font-size:12px;font-weight:700;letter-spacing:.02em}
.b-ok{background:rgba(52,211,153,.12);color:#34d399;border:1px solid rgba(52,211,153,.35)}
.b-warn{background:rgba(251,191,36,.1);color:#fbbf24;border:1px solid rgba(251,191,36,.3)}
.b-dim{background:#161b28;color:#8b93a7;border:1px solid #202839}
table{width:100%;border-collapse:collapse;margin-top:8px}
th{color:#8b93a7;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.08em;padding:9px 12px;border-bottom:1px solid #1b2232}
td{padding:11px 12px;border-bottom:1px solid #121826}
tr{transition:.15s}tr:hover td{background:rgba(122,162,255,.05)}
.score{font-weight:800;font-variant-numeric:tabular-nums}
.big{font-size:clamp(36px,6vw,52px);font-weight:900;line-height:1.05;
 background:linear-gradient(120deg,#34d399,#7aa2ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.card{background:rgba(16,21,33,.72);border:1px solid #1b2232;border-radius:16px;padding:20px;margin:14px 0;
 backdrop-filter:blur(8px);box-shadow:0 0 0 1px rgba(122,162,255,.03),0 8px 32px rgba(0,0,0,.35);transition:.25s}
.card:hover{border-color:rgba(52,211,153,.35);box-shadow:0 0 24px rgba(52,211,153,.07),0 8px 32px rgba(0,0,0,.35)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.kv .k{color:#8b93a7;font-size:11px;text-transform:uppercase;letter-spacing:.08em}
.kv .v{font-size:17px;font-weight:700;margin-top:2px;word-break:break-all}
.bar{height:8px;background:#161b28;border-radius:99px;overflow:hidden;margin-top:5px}
.bar>div{height:100%;background:linear-gradient(90deg,#34d399,#7aa2ff);box-shadow:0 0 10px rgba(52,211,153,.5)}
.mono{font-family:ui-monospace,SFMono-Regular,monospace;font-size:13px}
.foot{color:#5b6172;font-size:12px;margin-top:30px;border-top:1px solid #121826;padding-top:14px}
.tblwrap{overflow-x:auto}
button{background:linear-gradient(90deg,#34d399,#4f8df9);color:#06121c;font-weight:800;border:0;border-radius:10px;
 padding:10px 18px;cursor:pointer;transition:.2s;box-shadow:0 0 18px rgba(52,211,153,.25)}
button:hover{transform:translateY(-1px);box-shadow:0 0 26px rgba(52,211,153,.45)}
input{width:100%;padding:9px 10px;background:#0a0e18;border:1px solid #1b2232;border-radius:9px;color:#e8ecf4;transition:.2s}
input:focus{outline:none;border-color:#34d399;box-shadow:0 0 0 3px rgba(52,211,153,.12)}
.lang-sel{background:#0a0e18;border:1px solid #1b2232;color:#8b93a7;border-radius:8px;padding:5px 8px;font:600 12px ui-monospace,monospace;cursor:pointer}
.lang-sel:focus{outline:none;border-color:#34d399}
"""


NAV = ("<nav style='display:flex;gap:18px;align-items:center;margin-bottom:26px;font-weight:600'>"
       "<a href='/' style='font-weight:900;font-size:17px;letter-spacing:.02em'>"
       "<span style='color:#34d399'>◆</span> VERDIX</a>"
       "<span style='flex:1'></span>"
       "<a href='/web'>Directory</a><a href='/web/create'>Launch App</a>"
       "<a href='https://github.com/rexalpaundra0902-droid/verdix'>GitHub</a>" + LANG_SEL + "</nav>")


def page(title: str, body: str) -> str:
    return (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body>{NAV}{body}<p class='foot'>Verdix — verifiable economic memory for AI agents · "
            f"live data from BSC testnet &amp; Membase · "
            f"<a href='https://github.com/rexalpaundra0902-droid/verdix'>source</a> · testnet only, not investment advice</p>"
            f"{I18N_SCRIPT}</body></html>")


def score_badge(s: float) -> str:
    cls = "b-ok" if s >= 55 else ("b-warn" if s >= 30 else "b-dim")
    return f"<span class='badge {cls}'>{s:.1f}</span>"


def leaderboard_page(verdix_agents: list[dict], bitagents: list[dict]) -> str:
    vrows = "".join(
        f"<tr><td><a href='/web/agent/{a['agentId']}'>Agent #{a['agentId']}</a>"
        f"{' · smc-bot' if a['agentId'] == 1 else ''}"
        f"{' <span class=\"badge b-ok\">founding operator</span>' if a['agentId'] <= 7 else ''}</td>"
        f"<td class='score'>{score_badge(a['trustScore'])}</td>"
        f"<td>{a.get('n_subject', 0)} verified actions</td>"
        f"<td>{a.get('vdxStaked', 0):,.0f} VDX staked</td></tr>"
        for a in verdix_agents)
    brows = "".join(
        f"<tr><td><a href='/web/bitagent/{html.escape(str(b['handle']))}'>{html.escape(str(b['name'] or b['handle']))}</a></td>"
        f"<td class='score'>{score_badge(b['trustScore'])}</td>"
        f"<td>{int(b['raw_stats']['completed_jobs'])}/{int(b['raw_stats']['total_jobs'])} jobs</td>"
        f"<td>${b['raw_stats']['total_revenue_usd']:.4f}</td>"
        f"<td>{'🟢' if b.get('online') else '⚪'}</td></tr>"
        for b in bitagents)
    body = (
        "<h1>Verdix Trust Directory</h1>"
        "<p class='sub'>Trust scores for AI agents — computed from proofs, not claims. "
        "On-chain economic memory (BSC testnet) + verified payloads on Membase. "
        "<a href='/web/create'><b>→ Create your Verified Agent Vault</b></a></p>"
        "<h2>Verdix-native agents (full on-chain economic memory)</h2>"
        "<div class='tblwrap'><table><tr><th>Agent</th><th>Trust Score</th><th>History</th><th>Skin in the game</th></tr>"
        f"{vrows}</table></div>"
        f"<h2>BitAgent ecosystem (Unibase AIP, chain 97) — {len(bitagents)} agents</h2>"
        "<div class='tblwrap'><table><tr><th>Agent</th><th>Trust Score</th><th>Jobs</th><th>Revenue</th><th></th></tr>"
        f"{brows}</table></div>")
    return page("Verdix Trust Directory", body)


def _component_bars(components: dict[str, float]) -> str:
    out = ""
    for k, v in components.items():
        pct = max(0.0, min(1.0, float(v))) * 100
        out += (f"<div class='kv'><div class='k'>{html.escape(k)}</div>"
                f"<div class='v'>{float(v):.3f}</div><div class='bar'><div style='width:{pct:.0f}%'></div></div></div>")
    return out


def verdix_agent_page(p: dict, entries: list[dict], explorer: str, memory_addr: str) -> str:
    comp = {
        "success rate": p["success_rate"], "economic volume": p["economic_volume"],
        "counterparty diversity": p["counterparty_diversity"], "stress behavior": p["stress_behavior"],
        "dispute record": p["dispute_component"],
    }
    ent_rows = "".join(
        f"<tr><td class='mono'>#{e['entryId']}</td><td>C{e['actionClass']}/T{e['tier']}</td>"
        f"<td>{['✅ success','❌ failed','⚖️ for','⚖️ against'][e['outcome']]}</td>"
        f"<td class='mono'><a href='/memory/{e['dataHash']}'>{e['dataHash'][:18]}…</a></td></tr>"
        for e in entries[-15:][::-1])
    body = (
        f"<p><a href='/web'>← directory</a></p>"
        f"<h1>Verdix Agent #{p['agentId']}{' · smc-bot' if p['agentId'] == 1 else ''}</h1>"
        f"{'<p><span class=\"badge b-ok\">★ founding operator — permanent, original registry slot</span></p>' if p['agentId'] <= 7 else ''}"
        f"<p class='sub'>Identity ERC-8004 · economic memory on-chain · payloads on Membase</p>"
        f"<div class='card'><div class='grid'>"
        f"<div class='kv'><div class='k'>Trust Score</div><div class='big'>{p['trustScore']:.1f}</div></div>"
        f"<div class='kv'><div class='k'>Verified actions</div><div class='v'>{p['n_subject']}</div></div>"
        f"<div class='kv'><div class='k'>VDX staked</div><div class='v'>{p.get('vdxStaked', 0):,.0f}</div></div>"
        f"<div class='kv'><div class='k'>Disputes lost</div><div class='v'>{p['disputes_against']}</div></div>"
        f"<div class='kv'><div class='k'>Control changes</div><div class='v'>{p['n_control_changes']}</div></div>"
        f"</div></div>"
        f"<h2>Score components</h2><div class='card'><div class='grid'>{_component_bars(comp)}</div></div>"
        f"<h2>Economic memory (last 15)</h2>"
        f"<div class='tblwrap'><table><tr><th>Entry</th><th>Class/Tier</th><th>Outcome</th><th>Payload (verify)</th></tr>{ent_rows}</table></div>"
        f"<p class='sub' style='margin-top:12px'>Verify it yourself: "
        f"<a href='{explorer}/address/{memory_addr}#readContract'>EconomicMemory di BscScan</a> · "
        f"<a href='/agent/{p['agentId']}'>raw JSON</a> · <a href='/agent/{p['agentId']}/cv'>Economic CV</a></p>")
    return page(f"Verdix Agent #{p['agentId']}", body)


def bitagent_page(b: dict) -> str:
    comp = b["components"]
    onchain = b.get("identity_verified_onchain")
    ver = ("<span class='badge b-ok'>identity verified on-chain ✓</span>" if onchain
           else "<span class='badge b-warn'>identity not yet verified on-chain</span>")
    body = (
        f"<p><a href='/web'>← directory</a></p>"
        f"<h1>{html.escape(str(b['name'] or b['handle']))}</h1>"
        f"<p class='sub mono'>{html.escape(str(b['agent_id']))}</p>"
        f"<div class='card'><div class='grid'>"
        f"<div class='kv'><div class='k'>Trust Score</div><div class='big'>{b['trustScore']:.1f}</div></div>"
        f"<div class='kv'><div class='k'>Jobs</div><div class='v'>{int(b['raw_stats']['completed_jobs'])}/{int(b['raw_stats']['total_jobs'])}</div></div>"
        f"<div class='kv'><div class='k'>Revenue</div><div class='v'>${b['raw_stats']['total_revenue_usd']:.4f}</div></div>"
        f"<div class='kv'><div class='k'>Status</div><div class='v'>{'online' if b.get('online') else 'offline'}</div></div>"
        f"</div><p style='margin-top:10px'>{ver}</p></div>"
        f"<h2>Score components</h2><div class='card'><div class='grid'>{_component_bars(comp)}</div></div>"
        f"<p class='sub'>Source: {html.escape(b['source'])} · <a href='/bitagent/{html.escape(str(b['handle']))}'>raw JSON</a></p>")
    return page(f"{b['handle']} — Verdix Trust", body)
