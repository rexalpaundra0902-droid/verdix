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
    error SameController();

    constructor(AgentRegistry _registry, EconomicMemory _memoryLog) {
        registry = _registry;
        memoryLog = _memoryLog;
    }

    /// @notice Bayar agent lain. msg.sender harus controller dari fromAgentId.
    function pay(uint256 fromAgentId, uint256 toAgentId, bytes32 memo) external payable {
        if (!registry.isController(fromAgentId, msg.sender)) revert NotAgentOwner();
        if (fromAgentId == toAgentId) revert SelfPayment();
        if (msg.value == 0) revert ZeroAmount();

        address to = registry.controllerOf(toAgentId);
        // Re-audit 2026-07-21 H-A: cegah self-settlement wash — kalau penerima =
        // pengirim (controller sama antar dua agent milik 1 operator), dana
        // round-trip ke diri sendiri tapi mencetak entry Tier-1 palsu. Nol at-risk.
        if (to == msg.sender || to == registry.controllerOf(fromAgentId)) revert SameController();
        // Audit 2026-07-21 LOW-4: CEI — catat memory (efek) sebelum transfer
        // (interaksi). Router stateless jadi tak eksploitabel, tapi urutan ini
        // konsisten dan bikin event tak bisa berselang oleh reentrancy.
        memoryLog.record(
            fromAgentId,
            toAgentId,
            EconomicMemory.ActionClass.Settlement,
            1,
            uint128(msg.value),
            EconomicMemory.Outcome.Success,
            memo
        );
        (bool ok,) = to.call{value: msg.value}("");
        if (!ok) revert TransferFailed();

        emit Paid(fromAgentId, toAgentId, msg.value, memo);
    }
}
