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
contract VDXStaking {
    using SafeERC20 for IERC20;

    IERC20 public immutable vdx;
    AgentRegistry public immutable registry;
    uint64 public constant UNSTAKE_COOLDOWN = 7 days;

    struct Pending {
        uint128 amount;
        uint64 unlockAt;
    }

    mapping(uint256 => uint256) public stakedOf; // agentId => total staked aktif
    mapping(uint256 => Pending) public pendingOf; // agentId => unstake menunggu cooldown

    event Staked(uint256 indexed agentId, address indexed from, uint256 amount);
    event UnstakeRequested(uint256 indexed agentId, uint256 amount, uint64 unlockAt);
    event Unstaked(uint256 indexed agentId, address indexed to, uint256 amount);

    error UnknownAgent();
    error NotController();
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
        emit Staked(agentId, msg.sender, amount);
    }

    /// @notice Mulai unstake — dana terkunci selama cooldown dulu.
    function requestUnstake(uint256 agentId, uint256 amount) external {
        if (!registry.isController(agentId, msg.sender)) revert NotController();
        if (amount == 0) revert ZeroAmount();
        if (stakedOf[agentId] < amount) revert InsufficientStake();
        stakedOf[agentId] -= amount;
        Pending storage p = pendingOf[agentId];
        p.amount += uint128(amount);
        p.unlockAt = uint64(block.timestamp + UNSTAKE_COOLDOWN);
        emit UnstakeRequested(agentId, amount, p.unlockAt);
    }

    function claimUnstake(uint256 agentId) external {
        if (!registry.isController(agentId, msg.sender)) revert NotController();
        Pending storage p = pendingOf[agentId];
        if (p.amount == 0) revert NothingPending();
        if (block.timestamp < p.unlockAt) revert CooldownActive();
        uint256 amount = p.amount;
        delete pendingOf[agentId];
        vdx.safeTransfer(msg.sender, amount);
        emit Unstaked(agentId, msg.sender, amount);
    }
}
