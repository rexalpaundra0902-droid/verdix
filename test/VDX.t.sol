// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {AgentRegistry} from "../src/AgentRegistry.sol";
import {VDX} from "../src/VDX.sol";
import {VDXStaking} from "../src/VDXStaking.sol";

contract VDXTest is Test {
    AgentRegistry reg;
    VDX vdx;
    VDXStaking staking;

    address treasury = makeAddr("treasury");
    address bot = makeAddr("bot");
    address mallory = makeAddr("mallory");
    uint256 botId;

    function setUp() public {
        reg = new AgentRegistry();
        vdx = new VDX(treasury);
        staking = new VDXStaking(vdx, reg);
        vm.prank(bot);
        botId = reg.register("https://smc-bot.agents.verdix.io/agent.json");
        vm.prank(treasury);
        vdx.transfer(bot, 100_000e18);
    }

    function test_FixedSupply() public view {
        assertEq(vdx.totalSupply(), 500_000_000e18);
        assertEq(vdx.balanceOf(treasury), 500_000_000e18 - 100_000e18);
    }

    function test_StakeIncreasesSkinInTheGame() public {
        vm.startPrank(bot);
        vdx.approve(address(staking), 10_000e18);
        staking.stake(botId, 10_000e18);
        vm.stopPrank();
        assertEq(staking.stakedOf(botId), 10_000e18);
        assertEq(vdx.balanceOf(address(staking)), 10_000e18);
    }

    function test_StakeUnknownAgentReverts() public {
        vm.startPrank(bot);
        vdx.approve(address(staking), 1e18);
        vm.expectRevert(VDXStaking.UnknownAgent.selector);
        staking.stake(999, 1e18);
        vm.stopPrank();
    }

    /// Audit 2026-07-21 M4: hanya STAKER yang bisa menarik stake-nya sendiri.
    /// Pihak yang tak pernah stake (mallory) tak punya apa-apa untuk ditarik.
    function test_NonStakerCannotUnstake() public {
        vm.startPrank(bot);
        vdx.approve(address(staking), 10_000e18);
        staking.stake(botId, 10_000e18);
        vm.stopPrank();

        vm.prank(mallory);
        vm.expectRevert(VDXStaking.InsufficientStake.selector);
        staking.requestUnstake(botId, 5_000e18);
    }

    /// Cooldown 7 hari: stake tidak bisa kabur sesaat sebelum kena konsekuensi.
    function test_UnstakeCooldownEnforced() public {
        vm.startPrank(bot);
        vdx.approve(address(staking), 10_000e18);
        staking.stake(botId, 10_000e18);
        staking.requestUnstake(botId, 10_000e18);
        assertEq(staking.stakedOf(botId), 0); // langsung tidak dihitung skin-in-game

        vm.expectRevert(VDXStaking.CooldownActive.selector);
        staking.claimUnstake(botId);

        vm.warp(block.timestamp + 7 days);
        uint256 before = vdx.balanceOf(bot);
        staking.claimUnstake(botId);
        assertEq(vdx.balanceOf(bot), before + 10_000e18);
        vm.stopPrank();
    }

    /// Audit 2026-07-21 M4: stake TIDAK bisa dirampas controller baru. Identity
    /// dijual ke mallory, tapi stake milik bot tetap hak bot; mallory (staked 0)
    /// tak bisa menyentuhnya. (Dulu: controller baru menyapu stake voucher.)
    function test_StakeNotSeizableByNewController() public {
        vm.startPrank(bot);
        vdx.approve(address(staking), 10_000e18);
        staking.stake(botId, 10_000e18);
        reg.transferFrom(bot, mallory, botId);
        vm.stopPrank();

        // Controller baru tak punya stake → tak bisa menarik apa pun.
        vm.prank(mallory);
        vm.expectRevert(VDXStaking.InsufficientStake.selector);
        staking.requestUnstake(botId, 10_000e18);

        // Staker asli tetap bisa menarik miliknya sendiri.
        vm.prank(bot);
        staking.requestUnstake(botId, 10_000e18);
        assertEq(staking.stakeByStaker(botId, bot), 0);
    }

    function testFuzz_StakeAccounting(uint96 a, uint96 b) public {
        uint256 x = bound(a, 1, 50_000e18);
        uint256 y = bound(b, 1, 50_000e18);
        vm.startPrank(bot);
        vdx.approve(address(staking), x + y);
        staking.stake(botId, x);
        staking.stake(botId, y);
        vm.stopPrank();
        assertEq(staking.stakedOf(botId), x + y);
    }
}
