// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {AgentRegistry} from "../src/AgentRegistry.sol";
import {EconomicMemory} from "../src/EconomicMemory.sol";
import {RiskGuardVault} from "../src/RiskGuardVault.sol";

contract RiskGuardVaultTest is Test {
    AgentRegistry reg;
    EconomicMemory mem;
    RiskGuardVault vault;

    address principal = makeAddr("principal"); // manusia (Reku)
    address botKey = makeAddr("botKey"); // controller AI agent
    address venue = makeAddr("venue"); // exchange/venue whitelist
    address shady = makeAddr("shady"); // target non-whitelist
    uint256 botId;

    function setUp() public {
        vm.prank(principal);
        reg = new AgentRegistry();
        vm.prank(principal);
        mem = new EconomicMemory(reg);

        vm.prank(botKey);
        botId = reg.register("https://smc-bot.agents.verdix.io/agent.json");

        vm.prank(principal);
        vault = new RiskGuardVault(
            reg,
            mem,
            botId,
            RiskGuardVault.Policy({
                maxTxValue: 1 ether,
                dailyCap: 2 ether,
                cooldown: 1 hours,
                haltFloor: 5 ether
            })
        );
        vm.prank(principal);
        mem.setRecorder(address(vault), true);
        vm.prank(principal);
        vault.setTarget(venue, true);

        vm.deal(principal, 100 ether);
        vm.prank(principal);
        (bool ok,) = address(vault).call{value: 10 ether}("");
        assertTrue(ok);
    }

    function test_CompliantActionExecutesAndRecords() public {
        vm.prank(botKey);
        vault.act(venue, 1 ether, bytes32("open-long-btc"));

        assertEq(venue.balance, 1 ether);
        assertEq(mem.entryCount(), 1);
        EconomicMemory.Entry memory e = mem.getEntry(0);
        assertEq(e.agentId, botId);
        assertEq(e.tier, 1);
        assertEq(e.valueWei, 1 ether);
    }

    function test_OnlyManagerControllerCanAct() public {
        vm.prank(shady);
        vm.expectRevert(RiskGuardVault.NotManagerAgent.selector);
        vault.act(venue, 0.5 ether, bytes32(0));
        // principal pun tidak bisa act — dana keluar via jalur agent HARUS lewat policy
        vm.prank(principal);
        vm.expectRevert(RiskGuardVault.NotManagerAgent.selector);
        vault.act(venue, 0.5 ether, bytes32(0));
    }

    function test_NonWhitelistedTargetBlocked() public {
        vm.prank(botKey);
        vm.expectRevert(RiskGuardVault.TargetNotAllowed.selector);
        vault.act(shady, 0.5 ether, bytes32("exfil"));
    }

    function test_MaxTxBlocked() public {
        vm.prank(botKey);
        vm.expectRevert(RiskGuardVault.ExceedsMaxTx.selector);
        vault.act(venue, 1 ether + 1, bytes32("yolo"));
    }

    function test_DailyCapAccumulatesAndResets() public {
        vm.prank(botKey);
        vault.act(venue, 1 ether, bytes32("a1"));
        vm.warp(block.timestamp + 2 hours);
        vm.prank(botKey);
        vault.act(venue, 1 ether, bytes32("a2"));
        // 2 ether terpakai → cap habis
        vm.warp(block.timestamp + 2 hours);
        vm.prank(botKey);
        vm.expectRevert(RiskGuardVault.ExceedsDailyCap.selector);
        vault.act(venue, 0.1 ether, bytes32("a3"));
        // hari berikutnya reset
        vm.warp(block.timestamp + 1 days);
        vm.prank(botKey);
        vault.act(venue, 1 ether, bytes32("a4"));
    }

    function test_CooldownBlocked() public {
        vm.prank(botKey);
        vault.act(venue, 0.5 ether, bytes32("a1"));
        vm.prank(botKey);
        vm.expectRevert(RiskGuardVault.CooldownActive.selector);
        vault.act(venue, 0.5 ether, bytes32("burst"));
    }

    function test_HaltFloorProtectsCapital() public {
        // saldo 10, floor 5, cap 2/hari → agent mencoba spend terus tiap hari;
        // begitu aksi berikutnya akan menembus floor, vault menolak selamanya
        uint256 blocked = 0;
        for (uint256 i = 0; i < 5; i++) {
            vm.warp(block.timestamp + 1 days);
            vm.prank(botKey);
            try vault.act(venue, 1 ether, bytes32("d1")) {}
            catch {
                blocked++;
            }
            vm.warp(block.timestamp + 2 hours);
            vm.prank(botKey);
            try vault.act(venue, 1 ether, bytes32("d2")) {}
            catch {
                blocked++;
            }
        }
        // tepat 5 ether keluar (10 → floor 5), sisanya diblokir
        assertEq(address(vault).balance, 5 ether);
        assertEq(venue.balance, 5 ether);
        assertEq(blocked, 5);
    }

    function test_HaltFloorRevertsDirectly() public {
        vm.prank(principal);
        vault.setPolicy(
            RiskGuardVault.Policy({maxTxValue: 6 ether, dailyCap: 20 ether, cooldown: 0, haltFloor: 5 ether})
        );
        vm.prank(botKey);
        vm.expectRevert(RiskGuardVault.BreachesHaltFloor.selector);
        vault.act(venue, 5.5 ether, bytes32("breach"));
    }

    function test_OwnerAlwaysWithdraws() public {
        uint256 before = principal.balance;
        vm.prank(principal);
        vault.withdraw(10 ether); // owner bebas tarik, bahkan di bawah floor
        assertEq(principal.balance, before + 10 ether);
    }

    function test_OnlyOwnerSetsPolicy() public {
        vm.prank(botKey);
        vm.expectRevert(RiskGuardVault.NotOwner.selector);
        vault.setPolicy(RiskGuardVault.Policy({maxTxValue: 100 ether, dailyCap: 100 ether, cooldown: 0, haltFloor: 0}));
        vm.prank(botKey);
        vm.expectRevert(RiskGuardVault.NotOwner.selector);
        vault.setTarget(shady, true);
    }

    /// Agent yang identity-nya pindah tangan tidak otomatis pegang vault:
    /// controller berubah, dan key lama langsung kehilangan akses.
    function test_TransferredAgentControlFollows() public {
        address buyer = makeAddr("buyer");
        vm.prank(botKey);
        reg.transferFrom(botKey, buyer, botId);

        vm.prank(botKey);
        vm.expectRevert(RiskGuardVault.NotManagerAgent.selector);
        vault.act(venue, 0.5 ether, bytes32(0));

        vm.prank(buyer);
        vault.act(venue, 0.5 ether, bytes32("new-controller"));
    }

    function testFuzz_NeverBelowFloor(uint96 v) public {
        uint256 value = bound(v, 1, 1 ether);
        vm.prank(botKey);
        try vault.act(venue, value, bytes32("fz")) {} catch {}
        assertGe(address(vault).balance, 5 ether);
    }
}
