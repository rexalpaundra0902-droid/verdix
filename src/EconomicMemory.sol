// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {AgentRegistry} from "./AgentRegistry.sol";

/// @title EconomicMemory — Verdix Layer 2: CORE ASSET
/// @notice Append-only log perilaku ekonomi agent. Admission policy v8 di-enforce
///         by construction: agent TIDAK BISA menulis tentang dirinya sendiri —
///         hanya kontrak recorder resmi (PaymentRouter, TaskEscrow, dst) yang boleh
///         menulis, dan tiap recorder hanya menulis outcome yang ia saksikan sendiri
///         (settlement, escrow release, ruling arbitrator). Self-report = bukan memory.
contract EconomicMemory {
    /// Class per spec v8: 1 settled value transfer, 2 agreement w/ verifiable outcome,
    /// 3 adjudicated outcome, 4 observed behavior under stress.
    enum ActionClass {
        None,
        Settlement,
        Agreement,
        Adjudicated,
        Stress
    }

    enum Outcome {
        Success,
        Failed,
        DisputedFor,
        DisputedAgainst
    }

    struct Entry {
        uint64 entryId;
        uint256 agentId; // subjek: agent yang perilakunya dibuktikan entry ini
        uint256 counterpartyId; // 0 kalau tidak ada counterparty (mis. Class 4 stress event)
        ActionClass actionClass;
        uint8 tier; // 1 = settlement proof, 2 = escrowed, 3 = arbitrated, 4 = observed/attested
        uint128 valueWei;
        Outcome outcome;
        bytes32 dataHash; // hash payload off-chain (spec task, bukti, ruling)
        uint64 timestamp;
        address recorder;
    }

    AgentRegistry public immutable registry;
    address public owner;

    Entry[] private _entries;
    mapping(uint256 => uint64[]) private _entriesByAgent; // agentId => entry indices (subjek maupun counterparty)
    mapping(address => bool) public isRecorder;

    event RecorderSet(address indexed recorder, bool allowed);
    event ActionRecorded(
        uint64 indexed entryId,
        uint256 indexed agentId,
        uint256 indexed counterpartyId,
        ActionClass actionClass,
        uint8 tier,
        uint128 valueWei,
        Outcome outcome,
        bytes32 dataHash,
        address recorder
    );

    error NotOwner();
    error NotRecorder();
    error UnknownAgent();
    error BadClass();
    error BadTier();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(AgentRegistry _registry) {
        registry = _registry;
        owner = msg.sender;
    }

    function setOwner(address newOwner) external onlyOwner {
        owner = newOwner;
    }

    /// @notice Otorisasi kontrak recorder. Governance path: hanya kontrak yang
    ///         mekanisme verifikasinya sudah di-review yang boleh menulis memory.
    function setRecorder(address recorder, bool allowed) external onlyOwner {
        isRecorder[recorder] = allowed;
        emit RecorderSet(recorder, allowed);
    }

    /// @notice Tulis satu entry. Hanya recorder resmi.
    function record(
        uint256 agentId,
        uint256 counterpartyId,
        ActionClass actionClass,
        uint8 tier,
        uint128 valueWei,
        Outcome outcome,
        bytes32 dataHash
    ) external returns (uint64 entryId) {
        if (!isRecorder[msg.sender]) revert NotRecorder();
        if (actionClass == ActionClass.None) revert BadClass();
        if (tier == 0 || tier > 4) revert BadTier();
        if (!registry.exists(agentId)) revert UnknownAgent();
        if (counterpartyId != 0 && !registry.exists(counterpartyId)) revert UnknownAgent();

        entryId = uint64(_entries.length);
        _entries.push(
            Entry({
                entryId: entryId,
                agentId: agentId,
                counterpartyId: counterpartyId,
                actionClass: actionClass,
                tier: tier,
                valueWei: valueWei,
                outcome: outcome,
                dataHash: dataHash,
                timestamp: uint64(block.timestamp),
                recorder: msg.sender
            })
        );
        _entriesByAgent[agentId].push(entryId);
        if (counterpartyId != 0 && counterpartyId != agentId) {
            _entriesByAgent[counterpartyId].push(entryId);
        }
        emit ActionRecorded(
            entryId, agentId, counterpartyId, actionClass, tier, valueWei, outcome, dataHash, msg.sender
        );
    }

    function entryCount() external view returns (uint256) {
        return _entries.length;
    }

    function getEntry(uint64 entryId) external view returns (Entry memory) {
        return _entries[entryId];
    }

    function entryIdsOf(uint256 agentId) external view returns (uint64[] memory) {
        return _entriesByAgent[agentId];
    }

    function entriesOf(uint256 agentId) external view returns (Entry[] memory out) {
        uint64[] storage ids = _entriesByAgent[agentId];
        out = new Entry[](ids.length);
        for (uint256 i = 0; i < ids.length; i++) {
            out[i] = _entries[ids[i]];
        }
    }
}
