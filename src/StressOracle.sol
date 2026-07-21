// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AgentRegistry} from "./AgentRegistry.sol";
import {EconomicMemory} from "./EconomicMemory.sol";

/// @title StressOracle — Tier 4 recorder: observed behavior under stress (Class 4)
/// @notice Attestor terdaftar (off-chain data attestor per spec v8 Tier 3/4) menulis
///         event stress yang DIAMATI — drawdown, loss event, liquidation, recovery.
///         Ini tier bukti paling lemah, dan scorer memang memberinya bobot paling
///         rendah; nilainya ada di sinyal perilaku saat pasar stress, bukan volume.
contract StressOracle {
    AgentRegistry public immutable registry;
    EconomicMemory public immutable memoryLog;
    address public owner;
    address public pendingOwner;
    mapping(address => bool) public isAttestor;

    event AttestorSet(address indexed attestor, bool allowed);
    event StressAttested(uint256 indexed agentId, bytes32 dataHash, bool positiveOutcome);
    event OwnershipTransferStarted(address indexed previousOwner, address indexed newOwner);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error NotAttestor();
    error ZeroAddress();
    error NotPendingOwner();

    constructor(AgentRegistry _registry, EconomicMemory _memoryLog) {
        registry = _registry;
        memoryLog = _memoryLog;
        owner = msg.sender;
    }

    function setAttestor(address attestor, bool allowed) external {
        if (msg.sender != owner) revert NotOwner();
        isAttestor[attestor] = allowed;
        emit AttestorSet(attestor, allowed);
    }

    /// @notice Transfer ownership 2-langkah (audit 2026-07-21 HIGH-2) — owner
    ///         attestor-gate sebaiknya multisig; sebelumnya tak ada jalur transfer.
    function transferOwnership(address newOwner) external {
        if (msg.sender != owner) revert NotOwner();
        if (newOwner == address(0)) revert ZeroAddress();
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    function acceptOwnership() external {
        if (msg.sender != pendingOwner) revert NotPendingOwner();
        emit OwnershipTransferred(owner, pendingOwner);
        owner = pendingOwner;
        pendingOwner = address(0);
    }

    /// @param positiveOutcome true = agent keluar dari stress event dengan disiplin
    ///        (mis. loss ke-stop sesuai risk plan), false = breakdown (mis. liquidation).
    function attest(uint256 agentId, uint128 valueWei, bool positiveOutcome, bytes32 dataHash) external {
        if (!isAttestor[msg.sender]) revert NotAttestor();
        memoryLog.record(
            agentId,
            0,
            EconomicMemory.ActionClass.Stress,
            4,
            valueWei,
            positiveOutcome ? EconomicMemory.Outcome.Success : EconomicMemory.Outcome.Failed,
            dataHash
        );
        emit StressAttested(agentId, dataHash, positiveOutcome);
    }
}
