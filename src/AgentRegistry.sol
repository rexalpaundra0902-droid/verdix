// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title AgentRegistry — Verdix Layer 0: Identity
/// @notice ERC-8004-style identity registry: satu agentId on-chain per agent,
///         resolvable via domain atau address. Identity di sini sengaja tipis —
///         nilai Verdix ada di Economic Memory, bukan di registry (registry = commodity).
contract AgentRegistry {
    struct AgentInfo {
        uint256 agentId;
        string agentDomain;
        address agentAddress;
        uint64 registeredAt;
    }

    uint256 private _nextId = 1;
    mapping(uint256 => AgentInfo) private _agents;
    mapping(bytes32 => uint256) private _idByDomain; // keccak256(domain) => agentId
    mapping(address => uint256) private _idByAddress;

    event AgentRegistered(uint256 indexed agentId, string agentDomain, address indexed agentAddress);
    event AgentUpdated(uint256 indexed agentId, string agentDomain, address indexed agentAddress);

    error DomainTaken();
    error AddressTaken();
    error EmptyDomain();
    error UnknownAgent();
    error NotAgentOwner();

    /// @notice Daftarkan agent baru. msg.sender menjadi agentAddress —
    ///         agent harus mengontrol key-nya sendiri, tidak bisa didaftarkan pihak lain.
    function newAgent(string calldata agentDomain) external returns (uint256 agentId) {
        if (bytes(agentDomain).length == 0) revert EmptyDomain();
        bytes32 domainKey = keccak256(bytes(agentDomain));
        if (_idByDomain[domainKey] != 0) revert DomainTaken();
        if (_idByAddress[msg.sender] != 0) revert AddressTaken();

        agentId = _nextId++;
        _agents[agentId] = AgentInfo({
            agentId: agentId,
            agentDomain: agentDomain,
            agentAddress: msg.sender,
            registeredAt: uint64(block.timestamp)
        });
        _idByDomain[domainKey] = agentId;
        _idByAddress[msg.sender] = agentId;
        emit AgentRegistered(agentId, agentDomain, msg.sender);
    }

    /// @notice Rotasi address / ganti domain. Hanya agentAddress saat ini yang boleh.
    function updateAgent(uint256 agentId, string calldata newDomain, address newAddress) external {
        AgentInfo storage a = _agents[agentId];
        if (a.agentId == 0) revert UnknownAgent();
        if (msg.sender != a.agentAddress) revert NotAgentOwner();

        if (newAddress != address(0) && newAddress != a.agentAddress) {
            if (_idByAddress[newAddress] != 0) revert AddressTaken();
            delete _idByAddress[a.agentAddress];
            _idByAddress[newAddress] = agentId;
            a.agentAddress = newAddress;
        }
        if (bytes(newDomain).length != 0) {
            bytes32 newKey = keccak256(bytes(newDomain));
            if (_idByDomain[newKey] != 0 && _idByDomain[newKey] != agentId) revert DomainTaken();
            delete _idByDomain[keccak256(bytes(a.agentDomain))];
            _idByDomain[newKey] = agentId;
            a.agentDomain = newDomain;
        }
        emit AgentUpdated(agentId, a.agentDomain, a.agentAddress);
    }

    function getAgent(uint256 agentId) external view returns (AgentInfo memory a) {
        a = _agents[agentId];
        if (a.agentId == 0) revert UnknownAgent();
    }

    function resolveByDomain(string calldata agentDomain) external view returns (AgentInfo memory) {
        uint256 id = _idByDomain[keccak256(bytes(agentDomain))];
        if (id == 0) revert UnknownAgent();
        return _agents[id];
    }

    function resolveByAddress(address agentAddress) external view returns (AgentInfo memory) {
        uint256 id = _idByAddress[agentAddress];
        if (id == 0) revert UnknownAgent();
        return _agents[id];
    }

    function agentIdOf(address agentAddress) external view returns (uint256) {
        return _idByAddress[agentAddress];
    }

    function exists(uint256 agentId) external view returns (bool) {
        return _agents[agentId].agentId != 0;
    }

    function agentCount() external view returns (uint256) {
        return _nextId - 1;
    }
}
