// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "openzeppelin-contracts/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "openzeppelin-contracts/contracts/token/ERC20/utils/SafeERC20.sol";
import {AgentRegistry} from "./AgentRegistry.sol";

/// @title VDXStaking — skin in the game per agent (utility $VDX Phase 1)
/// @notice Siapa pun bisa stake VDX untuk sebuah agentId; hanya controller
///         agent yang bisa unstake, dengan cooldown supaya stake tidak bisa
///         kabur sesaat sebelum perilaku buruk ketahuan. Trust Intelligence
///         membaca stakedOf() sebagai komponen "skin in the game" — reputasi
///         yang ditopang modal yang bisa hangus lebih mahal untuk dipalsukan
///         (cost-of-forgery, konsisten spec v8).
///
/// @dev DUA KONSEKUENSI DESAIN YANG DISENGAJA — pahami sebelum stake:
///      1. Stake dari pihak ketiga = BACKING PERMANEN (vouching), bukan
///         deposito: yang bisa menarik hanya controller agent tersebut.
///         Jangan stake untuk agent yang tidak kamu percayai controllernya.
///      2. requestUnstake baru me-reset unlockAt untuk SELURUH pending —
///         request tambahan memperpanjang kunci pending sebelumnya (anti
///         gaming; unstake dicicil = cooldown ikut mundur).
contract VDXStaking {
    using SafeERC20 for IERC20;

    IERC20 public immutable vdx;
    AgentRegistry public immutable registry;
    uint64 public constant UNSTAKE_COOLDOWN = 7 days;

    struct Pending {
        uint128 amount;
        uint64 unlockAt;
    }

    mapping(uint256 => uint256) public stakedOf; // agentId => total staked aktif (agregat utk Trust score)
    // Audit 2026-07-21 M4: catat stake PER STAKER. Sebelumnya unstake di-gate
    // controller agent — controller NFT yang transferable bisa berubah ke pihak
    // asing setelah stake masuk, lalu merampas stake voucher. Sekarang HANYA
    // staker yang bisa menarik miliknya sendiri (vouching tetap bisa: voucher
    // pilih tidak menarik), dan controller baru tak bisa menyentuh stake orang.
    mapping(uint256 => mapping(address => uint256)) public stakeByStaker; // agentId => staker => aktif
    mapping(uint256 => mapping(address => Pending)) public pendingByStaker; // agentId => staker => pending

    event Staked(uint256 indexed agentId, address indexed from, uint256 amount);
    event UnstakeRequested(uint256 indexed agentId, address indexed staker, uint256 amount, uint64 unlockAt);
    event Unstaked(uint256 indexed agentId, address indexed to, uint256 amount);

    error UnknownAgent();
    error NothingPending();
    error CooldownActive();
    error InsufficientStake();
    error ZeroAmount();

    constructor(IERC20 _vdx, AgentRegistry _registry) {
        vdx = _vdx;
        registry = _registry;
    }

    function stake(uint256 agentId, uint256 amount) external {
        if (!registry.exists(agentId)) revert UnknownAgent();
        if (amount == 0) revert ZeroAmount();
        vdx.safeTransferFrom(msg.sender, address(this), amount);
        stakedOf[agentId] += amount;
        stakeByStaker[agentId][msg.sender] += amount;
        emit Staked(agentId, msg.sender, amount);
    }

    /// @notice Mulai unstake stake MILIKMU SENDIRI — dana terkunci cooldown dulu.
    function requestUnstake(uint256 agentId, uint256 amount) external {
        if (amount == 0) revert ZeroAmount();
        if (stakeByStaker[agentId][msg.sender] < amount) revert InsufficientStake();
        stakeByStaker[agentId][msg.sender] -= amount;
        stakedOf[agentId] -= amount;
        Pending storage p = pendingByStaker[agentId][msg.sender];
        p.amount += uint128(amount);
        p.unlockAt = uint64(block.timestamp + UNSTAKE_COOLDOWN);
        emit UnstakeRequested(agentId, msg.sender, amount, p.unlockAt);
    }

    function claimUnstake(uint256 agentId) external {
        Pending storage p = pendingByStaker[agentId][msg.sender];
        if (p.amount == 0) revert NothingPending();
        if (block.timestamp < p.unlockAt) revert CooldownActive();
        uint256 amount = p.amount;
        delete pendingByStaker[agentId][msg.sender];
        vdx.safeTransfer(msg.sender, amount);
        emit Unstaked(agentId, msg.sender, amount);
    }
}
