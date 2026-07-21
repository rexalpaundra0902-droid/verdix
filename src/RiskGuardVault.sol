// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AgentRegistry} from "./AgentRegistry.sol";
import {EconomicMemory} from "./EconomicMemory.sol";

/// @title RiskGuardVault — aplikasi pertama di atas Verdix
/// @notice Vault milik manusia yang dikelola AI agent (Verdix agentId), dengan
///         KONSTITUSI risk yang di-enforce on-chain — bukan janji di prompt:
///
///           maxTxValue   — batas nilai per aksi
///           dailyCap     — batas total per 24 jam
///           cooldown     — jeda minimum antar aksi
///           whitelist    — hanya venue/target yang disetujui owner
///           haltFloor    — saldo tidak boleh ditembus ke bawah (capital
///                          preservation floor — konsep floor-halt trading bot,
///                          dipindah jadi invariant on-chain)
///
///         Aksi yang melanggar policy REVERT — agent secanggih apa pun tidak
///         bisa melewatinya. Aksi yang lolos otomatis tercatat ke Verdix
///         Economic Memory (Class 1 / Tier 1, settlement = proof), jadi track
///         record si agent bisa diverifikasi siapa pun.
contract RiskGuardVault {
    struct Policy {
        uint128 maxTxValue;
        uint128 dailyCap;
        uint64 cooldown;
        uint128 haltFloor;
    }

    AgentRegistry public immutable registry;
    EconomicMemory public immutable memoryLog;
    address public owner; // principal manusia
    uint256 public managerAgentId; // AI agent pengelola

    Policy public policy;
    mapping(address => bool) public allowedTarget;

    uint128 public spentInWindow;
    uint64 public windowStart;
    uint64 public lastActionAt;

    uint256 private _lock = 1; // reentrancy guard (1=idle, 2=entered)

    event Deposited(address indexed from, uint256 amount);
    event Withdrawn(address indexed to, uint256 amount);
    event PolicySet(uint128 maxTxValue, uint128 dailyCap, uint64 cooldown, uint128 haltFloor);
    event TargetSet(address indexed target, bool allowed);
    event ManagerSet(uint256 indexed agentId);
    event AgentActed(uint256 indexed agentId, address indexed target, uint256 value, bytes32 memo);

    error NotOwner();
    error NotManagerAgent();
    error UnknownAgent();
    error TargetNotAllowed();
    error ExceedsMaxTx();
    error ExceedsDailyCap();
    error CooldownActive();
    error BreachesHaltFloor();
    error TransferFailed();
    error ZeroValue();
    error SelfDealing();
    error Reentrancy();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier nonReentrant() {
        if (_lock == 2) revert Reentrancy();
        _lock = 2;
        _;
        _lock = 1;
    }

    constructor(AgentRegistry _registry, EconomicMemory _memoryLog, uint256 _managerAgentId, Policy memory _policy) {
        registry = _registry;
        memoryLog = _memoryLog;
        owner = msg.sender;
        if (!_registry.exists(_managerAgentId)) revert UnknownAgent();
        managerAgentId = _managerAgentId;
        policy = _policy;
        emit ManagerSet(_managerAgentId);
        emit PolicySet(_policy.maxTxValue, _policy.dailyCap, _policy.cooldown, _policy.haltFloor);
    }

    receive() external payable {
        emit Deposited(msg.sender, msg.value);
    }

    // ---------- kontrol principal (owner selalu pegang kendali penuh) ----------

    function withdraw(uint256 amount) external onlyOwner nonReentrant {
        (bool ok,) = owner.call{value: amount}("");
        if (!ok) revert TransferFailed();
        emit Withdrawn(owner, amount);
    }

    function setPolicy(Policy calldata p) external onlyOwner {
        policy = p;
        emit PolicySet(p.maxTxValue, p.dailyCap, p.cooldown, p.haltFloor);
    }

    function setTarget(address target, bool allowed) external onlyOwner {
        allowedTarget[target] = allowed;
        emit TargetSet(target, allowed);
    }

    function setManager(uint256 agentId) external onlyOwner {
        if (!registry.exists(agentId)) revert UnknownAgent();
        managerAgentId = agentId;
        emit ManagerSet(agentId);
    }

    // ---------- aksi agent: satu-satunya pintu keluar dana selain owner ----------

    /// @notice AI agent mengeksekusi aksi (kirim dana ke venue whitelist).
    ///         Semua rule policy dicek on-chain; pelanggaran apa pun = revert.
    function act(address target, uint256 value, bytes32 memo) external nonReentrant {
        if (!registry.isController(managerAgentId, msg.sender)) revert NotManagerAgent();
        if (!allowedTarget[target]) revert TargetNotAllowed();
        // Audit 2026-07-21 HIGH-1: cegah fabrikasi Economic Memory. Settlement
        // value-0 bukan bukti apa pun; kirim ke owner/controller sendiri =
        // wash-trading (track record palsu tanpa aktivitas ekonomi riil).
        if (value == 0) revert ZeroValue();
        // Re-audit 2026-07-21 M-1: +target==address(this) — loopback ke receive()
        // vault sendiri = wash tanpa modal keluar.
        if (target == owner || target == msg.sender || target == address(this)) revert SelfDealing();
        if (value > policy.maxTxValue) revert ExceedsMaxTx();

        if (block.timestamp >= windowStart + 1 days) {
            windowStart = uint64(block.timestamp);
            spentInWindow = 0;
        }
        if (spentInWindow + value > policy.dailyCap) revert ExceedsDailyCap();
        if (lastActionAt != 0 && block.timestamp < lastActionAt + policy.cooldown) revert CooldownActive();
        if (address(this).balance - value < policy.haltFloor) revert BreachesHaltFloor();

        spentInWindow += uint128(value);
        lastActionAt = uint64(block.timestamp);

        (bool ok,) = target.call{value: value}("");
        if (!ok) revert TransferFailed();

        memoryLog.record(
            managerAgentId,
            0,
            EconomicMemory.ActionClass.Settlement,
            1,
            uint128(value),
            EconomicMemory.Outcome.Success,
            memo
        );
        emit AgentActed(managerAgentId, target, value, memo);
    }
}
