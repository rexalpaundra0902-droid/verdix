// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AgentRegistry} from "./AgentRegistry.sol";
import {EconomicMemory} from "./EconomicMemory.sol";

/// @title PaymentRouter — Tier 1 recorder: settlement adalah bukti
/// @notice Pembayaran agent→agent yang lewat sini otomatis tercatat di Economic
///         Memory sebagai Class 1 / Tier 1. Buktinya = transaksi itu sendiri;
///         tidak ada klaim yang perlu dipercaya.
contract PaymentRouter {
    AgentRegistry public immutable registry;
    EconomicMemory public immutable memoryLog;

    event Paid(uint256 indexed fromAgentId, uint256 indexed toAgentId, uint256 amount, bytes32 memo);

    error NotAgentOwner();
    error SelfPayment();
    error ZeroAmount();
    error TransferFailed();

    constructor(AgentRegistry _registry, EconomicMemory _memoryLog) {
        registry = _registry;
        memoryLog = _memoryLog;
    }

    /// @notice Bayar agent lain. msg.sender harus agentAddress dari fromAgentId.
    function pay(uint256 fromAgentId, uint256 toAgentId, bytes32 memo) external payable {
        if (registry.getAgent(fromAgentId).agentAddress != msg.sender) revert NotAgentOwner();
        if (fromAgentId == toAgentId) revert SelfPayment();
        if (msg.value == 0) revert ZeroAmount();

        address to = registry.getAgent(toAgentId).agentAddress;
        (bool ok,) = to.call{value: msg.value}("");
        if (!ok) revert TransferFailed();

        memoryLog.record(
            fromAgentId,
            toAgentId,
            EconomicMemory.ActionClass.Settlement,
            1,
            uint128(msg.value),
            EconomicMemory.Outcome.Success,
            memo
        );
        emit Paid(fromAgentId, toAgentId, msg.value, memo);
    }
}
