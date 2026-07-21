// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "openzeppelin-contracts/contracts/token/ERC721/ERC721.sol";
import {ECDSA} from "openzeppelin-contracts/contracts/utils/cryptography/ECDSA.sol";
import {MessageHashUtils} from "openzeppelin-contracts/contracts/utils/cryptography/MessageHashUtils.sol";

/// @title AgentRegistry — Verdix Layer 0: Identity (ERC-8004 draft surface)
/// @notice Agent = token ERC-721 per draft ERC-8004: register(agentURI) me-mint
///         agentId, owner NFT = owner agent, metadata key-value, dan operational
///         wallet terpisah via setAgentWallet (dengan tanda tangan wallet-nya).
///
///         Karena identity di ERC-8004 BY DESIGN transferable (NFT bisa dijual),
///         registry ini mencatat SETIAP perpindahan kontrol — transfer ownership,
///         set/unset wallet — di controlChangesOf(agentId). Trust Intelligence
///         memakai log itu untuk men-decay history yang diperoleh SEBELUM kontrol
///         pindah: skor mengikuti perilaku, bukan sekadar token yang bisa dibeli.
contract AgentRegistry is ERC721 {
    struct MetadataEntry {
        string metadataKey;
        bytes metadataValue;
    }

    uint256 private _nextId = 1;
    mapping(uint256 => string) private _agentURIs;
    mapping(uint256 => mapping(string => bytes)) private _metadata;
    mapping(uint256 => address) private _agentWallet; // operational wallet; 0 = pakai owner
    mapping(uint256 => uint64[]) private _controlChanges; // timestamp tiap perpindahan kontrol
    mapping(uint256 => uint256) public walletNonce; // audit LOW: anti-replay setAgentWallet
    mapping(address => uint256) private _walletAgent; // audit LOW: wallet operasional => agentId (keunikan)

    event Registered(uint256 indexed agentId, string agentURI, address indexed owner);
    event URIUpdated(uint256 indexed agentId, string newURI, address indexed updatedBy);
    event MetadataSet(
        uint256 indexed agentId, string indexed indexedMetadataKey, string metadataKey, bytes metadataValue
    );
    event AgentWalletSet(uint256 indexed agentId, address indexed wallet);
    event AgentWalletUnset(uint256 indexed agentId);
    event ControlChanged(uint256 indexed agentId, address indexed newController, string reason);

    error NotAgentOwner();
    error BadWalletSignature();
    error SignatureExpired();
    error WalletInUse();

    constructor() ERC721("Verdix Agent", "VDXA") {}

    modifier onlyAgentOwner(uint256 agentId) {
        if (_ownerOf(agentId) != msg.sender && !isApprovedForAll(_ownerOf(agentId), msg.sender)) {
            revert NotAgentOwner();
        }
        _;
    }

    // ---------- ERC-8004: registration ----------

    function register() external returns (uint256 agentId) {
        return _register("", new MetadataEntry[](0));
    }

    function register(string calldata agentURI) external returns (uint256 agentId) {
        return _register(agentURI, new MetadataEntry[](0));
    }

    function register(string calldata agentURI, MetadataEntry[] calldata metadata)
        external
        returns (uint256 agentId)
    {
        return _register(agentURI, metadata);
    }

    function _register(string memory agentURI, MetadataEntry[] memory metadata)
        private
        returns (uint256 agentId)
    {
        agentId = _nextId++;
        _safeMint(msg.sender, agentId);
        _agentURIs[agentId] = agentURI;
        for (uint256 i = 0; i < metadata.length; i++) {
            _metadata[agentId][metadata[i].metadataKey] = metadata[i].metadataValue;
            emit MetadataSet(agentId, metadata[i].metadataKey, metadata[i].metadataKey, metadata[i].metadataValue);
        }
        emit Registered(agentId, agentURI, msg.sender);
    }

    // ---------- ERC-8004: URI + metadata ----------

    function setAgentURI(uint256 agentId, string calldata newURI) external onlyAgentOwner(agentId) {
        _agentURIs[agentId] = newURI;
        emit URIUpdated(agentId, newURI, msg.sender);
    }

    function tokenURI(uint256 agentId) public view override returns (string memory) {
        _requireOwned(agentId);
        return _agentURIs[agentId];
    }

    function getMetadata(uint256 agentId, string memory metadataKey) external view returns (bytes memory) {
        return _metadata[agentId][metadataKey];
    }

    function setMetadata(uint256 agentId, string memory metadataKey, bytes memory metadataValue)
        external
        onlyAgentOwner(agentId)
    {
        _metadata[agentId][metadataKey] = metadataValue;
        emit MetadataSet(agentId, metadataKey, metadataKey, metadataValue);
    }

    // ---------- ERC-8004: operational wallet ----------

    /// @notice Pasang wallet operasional. Wajib bawa tanda tangan si wallet
    ///         (consent), supaya tidak bisa "menunjuk" wallet orang lain.
    function setAgentWallet(uint256 agentId, address newWallet, uint256 deadline, bytes calldata signature)
        external
        onlyAgentOwner(agentId)
    {
        if (block.timestamp > deadline) revert SignatureExpired();
        // Audit 2026-07-21 LOW: nonce per-agent supaya signature tidak bisa
        // di-replay (mis. pasang ulang wallet lama pasca-unset dalam deadline).
        uint256 nonce = walletNonce[agentId];
        bytes32 digest = MessageHashUtils.toEthSignedMessageHash(
            keccak256(
                abi.encode("VerdixAgentWallet", block.chainid, address(this), agentId, newWallet, nonce, deadline)
            )
        );
        if (ECDSA.recover(digest, signature) != newWallet) revert BadWalletSignature();
        // Audit 2026-07-21 LOW: keunikan wallet operasional (enforce WalletInUse
        // yang sebelumnya dideklarasi tapi mati) — cegah 1 wallet jadi controller
        // banyak agent (sybil reputasi).
        uint256 boundTo = _walletAgent[newWallet];
        if (boundTo != 0 && boundTo != agentId) revert WalletInUse();
        address old = _agentWallet[agentId];
        if (old != address(0)) _walletAgent[old] = 0;
        walletNonce[agentId] = nonce + 1;
        _agentWallet[agentId] = newWallet;
        _walletAgent[newWallet] = agentId;
        _logControlChange(agentId, newWallet, "wallet_set");
        emit AgentWalletSet(agentId, newWallet);
    }

    function unsetAgentWallet(uint256 agentId) external onlyAgentOwner(agentId) {
        address old = _agentWallet[agentId];
        if (old != address(0)) _walletAgent[old] = 0;
        delete _agentWallet[agentId];
        _logControlChange(agentId, _ownerOf(agentId), "wallet_unset");
        emit AgentWalletUnset(agentId);
    }

    function getAgentWallet(uint256 agentId) public view returns (address) {
        address w = _agentWallet[agentId];
        return w != address(0) ? w : _ownerOf(agentId);
    }

    // ---------- Verdix: kontrol & recorder hooks ----------

    /// @notice Address yang dianggap "bertindak sebagai" agent oleh recorder Verdix.
    function controllerOf(uint256 agentId) external view returns (address) {
        _requireOwned(agentId);
        return getAgentWallet(agentId);
    }

    function isController(uint256 agentId, address who) external view returns (bool) {
        return _ownerOf(agentId) != address(0) && getAgentWallet(agentId) == who;
    }

    function exists(uint256 agentId) external view returns (bool) {
        return _ownerOf(agentId) != address(0);
    }

    function agentCount() external view returns (uint256) {
        return _nextId - 1;
    }

    /// @notice Timestamp tiap perpindahan kontrol — input wajib Trust Intelligence.
    function controlChangesOf(uint256 agentId) external view returns (uint64[] memory) {
        return _controlChanges[agentId];
    }

    function _logControlChange(uint256 agentId, address newController, string memory reason) private {
        _controlChanges[agentId].push(uint64(block.timestamp));
        emit ControlChanged(agentId, newController, reason);
    }

    /// @dev Transfer NFT = kontrol pindah: catat, dan wallet lama ikut dicabut
    ///      (owner baru tidak boleh mewarisi wallet operasional owner lama).
    function _update(address to, uint256 tokenId, address auth) internal override returns (address from) {
        from = super._update(to, tokenId, auth);
        if (from != address(0) && to != address(0)) {
            address old = _agentWallet[tokenId];
            if (old != address(0)) _walletAgent[old] = 0; // audit LOW: lepas keunikan
            delete _agentWallet[tokenId];
            _logControlChange(tokenId, to, "ownership_transfer");
        }
    }
}
