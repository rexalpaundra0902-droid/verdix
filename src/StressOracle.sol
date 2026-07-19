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
    mapping(address => bool) public isAttestor;

    event AttestorSet(address indexed attestor, bool allowed);
    event StressAttested(uint256 indexed agentId, bytes32 dataHash, bool positiveOutcome);

    error NotOwner();
    error NotAttestor();

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
