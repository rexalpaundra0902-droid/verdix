// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AgentRegistry} from "./AgentRegistry.sol";
import {EconomicMemory} from "./EconomicMemory.sol";

/// @title VaultFactory — "Verdix Verified Agent", self-serve
/// @notice Siapa pun bisa spin RiskGuardVault-nya sendiri: pilih agent (ERC-8004),
///         set konstitusi risk, deposit — dan SETIAP aksi agent di vault otomatis
///         tercatat ke Economic Memory sebagai track record terverifikasi.
///
///         Factory-lah yang menjadi recorder resmi di EconomicMemory; vault anak
///         menulis lewat `recordAction`, dan factory hanya menerima dari vault
///         yang ia deploy sendiri (`isVault`). Dengan begitu otorisasi recorder
///         cukup SEKALI (factory), tanpa per-vault governance, dan vault palsu
///         yang bukan buatan factory tidak akan pernah bisa menulis memory.
contract VaultFactory {
    AgentRegistry public immutable registry;
    EconomicMemory public immutable memoryLog;

    address[] public allVaults;
    mapping(address => bool) public isVault;
    mapping(address => address[]) public vaultsOfOwner;
    mapping(uint256 => address[]) public vaultsOfAgent;

    event VaultCreated(
        address indexed vault, address indexed owner, uint256 indexed managerAgentId, GuardedVault.Policy policy
    );
    event ActionRecorded(address indexed vault, uint256 indexed agentId, uint256 value, bytes32 memo);

    error NotAVault();
    error AgentMismatch();

    constructor(AgentRegistry _registry, EconomicMemory _memoryLog) {
        registry = _registry;
        memoryLog = _memoryLog;
    }

    /// @notice Bikin vault berpolicy milikmu sendiri. msg.value (opsional) jadi deposit awal.
    function createVault(uint256 managerAgentId, GuardedVault.Policy calldata policy)
        external
        payable
        returns (address vault)
    {
        // Audit 2026-07-21 LOW-6 (diterima sebagai risiko): SENGAJA tidak
        // memaksa msg.sender == controller(managerAgentId). Pola sah: principal
        // (owner vault) BEDA dari controller agent (kunci operasional AI yang
        // ia sewa). Grief atribusi vaultsOfAgent murni kosmetik — vault palsu
        // tetap tak bisa menulis memory (act butuh isController). UI listing
        // harus verifikasi kepemilikan sebelum menampilkan, bukan kontrak.
        GuardedVault v = new GuardedVault{value: msg.value}(registry, this, msg.sender, managerAgentId, policy);
        vault = address(v);
        isVault[vault] = true;
        allVaults.push(vault);
        vaultsOfOwner[msg.sender].push(vault);
        vaultsOfAgent[managerAgentId].push(vault);
        emit VaultCreated(vault, msg.sender, managerAgentId, policy);
    }

    /// @notice Dipanggil vault anak setiap aksi compliant → entry Tier-1 di Economic Memory.
    function recordAction(uint256 agentId, uint128 valueWei, bytes32 memo) external {
        if (!isVault[msg.sender]) revert NotAVault();
        // Audit 2026-07-21 M6: jangan percaya argumen agentId — derive dari
        // vault pemanggil. Tanpa ini, varian vault yang kelak di-isVault bisa
        // menulis reputasi atas agentId milik korban.
        if (agentId != GuardedVault(payable(msg.sender)).managerAgentId()) revert AgentMismatch();
        memoryLog.record(
            agentId, 0, EconomicMemory.ActionClass.Settlement, 1, valueWei, EconomicMemory.Outcome.Success, memo
        );
        emit ActionRecorded(msg.sender, agentId, valueWei, memo);
    }

    function vaultCount() external view returns (uint256) {
        return allVaults.length;
    }

    function vaultsOf(address owner) external view returns (address[] memory) {
        return vaultsOfOwner[owner];
    }

    function agentVaults(uint256 agentId) external view returns (address[] memory) {
        return vaultsOfAgent[agentId];
    }
}

/// @title GuardedVault — RiskGuardVault generasi self-serve (anak VaultFactory)
/// @notice Identik secara policy dgn RiskGuardVault: konstitusi risk on-chain
///         yang agent tidak bisa langgar. Bedanya: menulis memory via factory,
///         dan owner ditentukan saat create (bukan deployer).
contract GuardedVault {
    struct Policy {
        uint128 maxTxValue;
        uint128 dailyCap;
        uint64 cooldown;
        uint128 haltFloor;
    }

    AgentRegistry public immutable registry;
    VaultFactory public immutable factory;
    address public owner;
    uint256 public managerAgentId;

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

    constructor(
        AgentRegistry _registry,
        VaultFactory _factory,
        address _owner,
        uint256 _managerAgentId,
        Policy memory _policy
    ) payable {
        registry = _registry;
        factory = _factory;
        owner = _owner;
        if (!_registry.exists(_managerAgentId)) revert UnknownAgent();
        managerAgentId = _managerAgentId;
        policy = _policy;
        emit ManagerSet(_managerAgentId);
        emit PolicySet(_policy.maxTxValue, _policy.dailyCap, _policy.cooldown, _policy.haltFloor);
        if (msg.value > 0) emit Deposited(_owner, msg.value);
    }

    receive() external payable {
        emit Deposited(msg.sender, msg.value);
    }

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

    /// @notice Aksi agent — semua rule dicek on-chain; pelanggaran = revert;
    ///         aksi lolos = track record terverifikasi (via factory → EconomicMemory).
    function act(address target, uint256 value, bytes32 memo) external nonReentrant {
        if (!registry.isController(managerAgentId, msg.sender)) revert NotManagerAgent();
        if (!allowedTarget[target]) revert TargetNotAllowed();
        // Audit 2026-07-21 HIGH-1: value-0 bukan bukti; kirim ke owner/controller
        // sendiri = wash-trading track record. Lihat RiskGuardVault.act.
        if (value == 0) revert ZeroValue();
        // Re-audit 2026-07-21 M-1: +target==address(this) (loopback wash).
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

        factory.recordAction(managerAgentId, uint128(value), memo);
        emit AgentActed(managerAgentId, target, value, memo);
    }
}
