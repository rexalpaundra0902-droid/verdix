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

    AgentRegistry public immutable registry;
    EconomicMemory public immutable memoryLog;
    address public owner;
    address public arbitrator;

    uint256 private _nextTaskId = 1;
    mapping(uint256 => Task) public tasks;

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

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(AgentRegistry _registry, EconomicMemory _memoryLog, address _arbitrator) {
        registry = _registry;
        memoryLog = _memoryLog;
        owner = msg.sender;
        arbitrator = _arbitrator;
    }

    function setArbitrator(address _arbitrator) external onlyOwner {
        arbitrator = _arbitrator;
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
        registry.controllerOf(workerId); // revert kalau worker tidak terdaftar
        if (deadline <= block.timestamp) revert BadDeadline();
        if (payment == 0) revert BadValue();
        uint128 clientBond = bondOf(payment);
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

        memoryLog.record(
            t.workerId,
            t.clientId,
            EconomicMemory.ActionClass.Agreement,
            2,
            t.payment,
            EconomicMemory.Outcome.Success,
            t.specHash
        );
        memoryLog.record(
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
        memoryLog.record(
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
            t.status = Status.Expired;
            _send(clientAddr, uint256(t.payment) + t.clientBond + t.workerBond);
            memoryLog.record(
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
