// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AgentRegistry} from "./AgentRegistry.sol";
import {EconomicMemory} from "./EconomicMemory.sol";

/// @title TaskEscrow — Tier 2/3 recorder: delegasi task antar agent
/// @notice Anti-farming per spec v8: entry "task selesai" hanya bisa lahir dari
///         escrow yang benar-benar mengunci payment + bond DUA SISI. Memalsukan
///         satu entry berarti mengunci modal + gas + risiko slash — Trust Score
///         yang didapat harus selalu lebih murah daripada biaya memalsukannya
///         (cost-of-forgery principle). Dispute diputus arbitrator = Tier 3.
contract TaskEscrow {
    enum Status {
        None,
        Open,
        Accepted,
        Confirmed,
        Disputed,
        Resolved,
        Expired,
        Cancelled
    }

    struct Task {
        uint256 clientId;
        uint256 workerId;
        uint128 payment;
        uint128 clientBond;
        uint128 workerBond;
        uint64 deadline;
        Status status;
        bytes32 specHash;
    }

    uint256 public constant BOND_BPS = 1000; // bond 10% dari payment, dua sisi
    // Audit 2026-07-21 M1: worker punya jendela dispute yang tak bisa di-front-run
    // oleh expire() setelah deadline (client tak bisa rampas bond dgn balapan gas).
    uint64 public constant DISPUTE_GRACE = 1 hours;
    // Audit 2026-07-21 M2: kalau arbitrator hilang/tak merespons, dana dispute
    // tak boleh terkunci selamanya — setelah timeout ini bisa dibubarkan adil.
    uint64 public constant DISPUTE_TIMEOUT = 30 days;

    AgentRegistry public immutable registry;
    EconomicMemory public immutable memoryLog;
    address public owner;
    address public arbitrator;

    uint256 private _nextTaskId = 1;
    mapping(uint256 => Task) public tasks;
    mapping(uint256 => uint64) public disputedAt; // taskId => waktu dispute diangkat

    event TaskCreated(
        uint256 indexed taskId, uint256 indexed clientId, uint256 indexed workerId, uint128 payment, uint64 deadline
    );
    event TaskAccepted(uint256 indexed taskId);
    event TaskConfirmed(uint256 indexed taskId);
    event TaskDisputed(uint256 indexed taskId, uint256 indexed byAgentId);
    event TaskRuled(uint256 indexed taskId, bool workerWins);
    event TaskExpired(uint256 indexed taskId);
    event TaskCancelled(uint256 indexed taskId);

    error NotOwner();
    error NotArbitrator();
    error NotAgentOwner();
    error BadStatus();
    error BadDeadline();
    error BadValue();
    error SelfDelegation();
    error DeadlineNotPassed();
    error DeadlinePassed();
    error TransferFailed();
    error ZeroAddress();
    error DisputeNotTimedOut();
    error SameController();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(AgentRegistry _registry, EconomicMemory _memoryLog, address _arbitrator) {
        if (_arbitrator == address(0)) revert ZeroAddress(); // audit M2
        registry = _registry;
        memoryLog = _memoryLog;
        owner = msg.sender;
        arbitrator = _arbitrator;
    }

    function setArbitrator(address _arbitrator) external onlyOwner {
        if (_arbitrator == address(0)) revert ZeroAddress(); // audit M2
        arbitrator = _arbitrator;
    }

    /// @dev Audit 2026-07-21 M3: penulisan Economic Memory TIDAK boleh memblokir
    ///      pelepasan dana. Kalau escrow dicabut sebagai recorder saat task
    ///      in-flight, settlement tetap jalan; entry memory dilewati (best-effort).
    function _tryRecord(
        uint256 agentId,
        uint256 counterpartyId,
        EconomicMemory.ActionClass actionClass,
        uint8 tier,
        uint128 valueWei,
        EconomicMemory.Outcome outcome,
        bytes32 dataHash
    ) private {
        try memoryLog.record(agentId, counterpartyId, actionClass, tier, valueWei, outcome, dataHash) returns (uint64) {}
        catch {}
    }

    function bondOf(uint128 payment) public pure returns (uint128) {
        return uint128((uint256(payment) * BOND_BPS) / 10_000);
    }

    /// @notice Client buka task: kunci payment + bond client sekaligus.
    function createTask(uint256 clientId, uint256 workerId, uint128 payment, uint64 deadline, bytes32 specHash)
        external
        payable
        returns (uint256 taskId)
    {
        if (!registry.isController(clientId, msg.sender)) revert NotAgentOwner();
        if (clientId == workerId) revert SelfDelegation();
        // Re-audit 2026-07-21 H-B: satu operator (1 controller EOA) memegang
        // client-agent DAN worker-agent berbeda → siklus escrow net-0 mencetak
        // entry Tier-2 palsu. Larang kedua sisi berbagi controller.
        if (registry.controllerOf(clientId) == registry.controllerOf(workerId)) revert SameController();
        if (deadline <= block.timestamp) revert BadDeadline();
        if (payment == 0) revert BadValue();
        uint128 clientBond = bondOf(payment);
        // Re-audit 2026-07-21 M-2: bondOf = payment/10 truncate ke 0 utk payment
        // < 10 wei → worker tanpa skin-in-the-game. Wajib bond > 0.
        if (clientBond == 0) revert BadValue();
        if (msg.value != uint256(payment) + clientBond) revert BadValue();

        taskId = _nextTaskId++;
        tasks[taskId] = Task({
            clientId: clientId,
            workerId: workerId,
            payment: payment,
            clientBond: clientBond,
            workerBond: bondOf(payment),
            deadline: deadline,
            status: Status.Open,
            specHash: specHash
        });
        emit TaskCreated(taskId, clientId, workerId, payment, deadline);
    }

    /// @notice Worker terima task: kunci bond worker.
    function acceptTask(uint256 taskId) external payable {
        Task storage t = tasks[taskId];
        if (t.status != Status.Open) revert BadStatus();
        if (!registry.isController(t.workerId, msg.sender)) revert NotAgentOwner();
        // Re-audit 2026-07-21 H-B: controller worker bisa berubah jadi = controller
        // client SETELAH createTask (transfer/setWallet) → cek ulang saat accept.
        if (registry.controllerOf(t.clientId) == registry.controllerOf(t.workerId)) revert SameController();
        if (block.timestamp >= t.deadline) revert DeadlinePassed();
        if (msg.value != t.workerBond) revert BadValue();
        t.status = Status.Accepted;
        emit TaskAccepted(taskId);
    }

    /// @notice Client konfirmasi selesai → payout + tulis memory (worker Tier 2, client Tier 1).
    function confirm(uint256 taskId) external {
        Task storage t = tasks[taskId];
        if (t.status != Status.Accepted) revert BadStatus();
        if (!registry.isController(t.clientId, msg.sender)) revert NotAgentOwner();
        t.status = Status.Confirmed;

        _send(registry.controllerOf(t.workerId), uint256(t.payment) + t.workerBond);
        _send(msg.sender, t.clientBond);

        _tryRecord(
            t.workerId,
            t.clientId,
            EconomicMemory.ActionClass.Agreement,
            2,
            t.payment,
            EconomicMemory.Outcome.Success,
            t.specHash
        );
        _tryRecord(
            t.clientId,
            t.workerId,
            EconomicMemory.ActionClass.Settlement,
            1,
            t.payment,
            EconomicMemory.Outcome.Success,
            t.specHash
        );
        emit TaskConfirmed(taskId);
    }

    /// @notice Salah satu pihak angkat dispute → menunggu ruling arbitrator.
    function dispute(uint256 taskId) external {
        Task storage t = tasks[taskId];
        if (t.status != Status.Accepted) revert BadStatus();
        uint256 byAgent;
        if (registry.isController(t.clientId, msg.sender)) byAgent = t.clientId;
        else if (registry.isController(t.workerId, msg.sender)) byAgent = t.workerId;
        else revert NotAgentOwner();
        t.status = Status.Disputed;
        disputedAt[taskId] = uint64(block.timestamp);
        emit TaskDisputed(taskId, byAgent);
    }

    /// @notice Ruling arbitrator (Tier 3). Bond pihak yang kalah → pemenang.
    function rule(uint256 taskId, bool workerWins) external {
        if (msg.sender != arbitrator) revert NotArbitrator();
        Task storage t = tasks[taskId];
        if (t.status != Status.Disputed) revert BadStatus();
        t.status = Status.Resolved;

        address clientAddr = registry.controllerOf(t.clientId);
        address workerAddr = registry.controllerOf(t.workerId);

        if (workerWins) {
            _send(workerAddr, uint256(t.payment) + t.workerBond + t.clientBond);
        } else {
            _send(clientAddr, uint256(t.payment) + t.clientBond + t.workerBond);
        }
        _tryRecord(
            t.workerId,
            t.clientId,
            EconomicMemory.ActionClass.Adjudicated,
            3,
            t.payment,
            workerWins ? EconomicMemory.Outcome.DisputedFor : EconomicMemory.Outcome.DisputedAgainst,
            t.specHash
        );
        emit TaskRuled(taskId, workerWins);
    }

    /// @notice Lewat deadline tanpa konfirmasi = kegagalan worker yang terverifikasi
    ///         (Class 2, failure condition terpenuhi). Siapa pun boleh trigger.
    function expire(uint256 taskId) external {
        Task storage t = tasks[taskId];
        if (block.timestamp < t.deadline) revert DeadlineNotPassed();
        address clientAddr = registry.controllerOf(t.clientId);

        if (t.status == Status.Open) {
            t.status = Status.Expired;
            _send(clientAddr, uint256(t.payment) + t.clientBond);
        } else if (t.status == Status.Accepted) {
            // Audit 2026-07-21 M1: task Accepted lewat-deadline hanya bisa
            // di-expire SETELAH DISPUTE_GRACE — kalau tidak, client bisa
            // front-run tx dispute() worker (gas lebih tinggi) tepat di blok
            // deadline untuk merampas workerBond + kerja gratis. Grace ini
            // menjamin worker punya jendela dispute yang tak bisa dibalap.
            if (block.timestamp < uint256(t.deadline) + DISPUTE_GRACE) revert DeadlineNotPassed();
            t.status = Status.Expired;
            _send(clientAddr, uint256(t.payment) + t.clientBond + t.workerBond);
            _tryRecord(
                t.workerId,
                t.clientId,
                EconomicMemory.ActionClass.Agreement,
                2,
                t.payment,
                EconomicMemory.Outcome.Failed,
                t.specHash
            );
        } else {
            revert BadStatus();
        }
        emit TaskExpired(taskId);
    }

    /// @notice Audit 2026-07-21 M2: escape-hatch kalau arbitrator hilang. Setelah
    ///         DISPUTE_TIMEOUT tanpa ruling, siapa pun boleh membubarkan dispute
    ///         secara ADIL: tiap pihak menerima kembali dana miliknya sendiri
    ///         (client: payment+clientBond, worker: workerBond). Tak ada pemenang
    ///         → tak ada entry reputasi (dispute tak terselesaikan bukan bukti).
    function expireDispute(uint256 taskId) external {
        Task storage t = tasks[taskId];
        if (t.status != Status.Disputed) revert BadStatus();
        if (block.timestamp < uint256(disputedAt[taskId]) + DISPUTE_TIMEOUT) revert DisputeNotTimedOut();
        t.status = Status.Expired;
        _send(registry.controllerOf(t.clientId), uint256(t.payment) + t.clientBond);
        _send(registry.controllerOf(t.workerId), t.workerBond);
        emit TaskExpired(taskId);
    }

    /// @notice Client batalkan sebelum worker accept — belum ada komitmen, tidak ada entry.
    function cancel(uint256 taskId) external {
        Task storage t = tasks[taskId];
        if (t.status != Status.Open) revert BadStatus();
        if (!registry.isController(t.clientId, msg.sender)) revert NotAgentOwner();
        t.status = Status.Cancelled;
        _send(msg.sender, uint256(t.payment) + t.clientBond);
        emit TaskCancelled(taskId);
    }

    function _send(address to, uint256 amount) private {
        (bool ok,) = to.call{value: amount}("");
        if (!ok) revert TransferFailed();
    }
}
