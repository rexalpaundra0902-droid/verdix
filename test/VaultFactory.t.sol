// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {AgentRegistry} from "../src/AgentRegistry.sol";
import {EconomicMemory} from "../src/EconomicMemory.sol";
import {VaultFactory, GuardedVault} from "../src/VaultFactory.sol";

contract VaultFactoryTest is Test {
    AgentRegistry reg;
    EconomicMemory mem;
    VaultFactory factory;

    address deployer = makeAddr("deployer");
    address alice = makeAddr("alice"); // pemilik vault (principal)
    address botKey = makeAddr("botKey"); // controller agent
    address venue = makeAddr("venue");
    address mallory = makeAddr("mallory");
    uint256 botId;

    GuardedVault.Policy P = GuardedVault.Policy({
        maxTxValue: 1 ether,
        dailyCap: 2 ether,
        cooldown: 0,
        haltFloor: 1 ether
    });

    function setUp() public {
        vm.startPrank(deployer);
        reg = new AgentRegistry();
        mem = new EconomicMemory(reg);
        factory = new VaultFactory(reg, mem);
        mem.setRecorder(address(factory), true); // otorisasi SEKALI utk semua vault anak
        vm.stopPrank();

        vm.prank(botKey);
        botId = reg.register("https://bot.agents.verdix.io/agent.json");
        vm.deal(alice, 100 ether);
        vm.deal(mallory, 100 ether);
    }

    function _create() internal returns (GuardedVault v) {
        vm.prank(alice);
        address addr = factory.createVault{value: 5 ether}(botId, P);
        v = GuardedVault(payable(addr));
        vm.prank(alice);
        v.setTarget(venue, true);
    }

    function test_AnyoneCanCreateOwnVault() public {
        GuardedVault v = _create();
        assertEq(v.owner(), alice);
        assertEq(address(v).balance, 5 ether);
        assertEq(factory.vaultCount(), 1);
        assertTrue(factory.isVault(address(v)));
        assertEq(factory.vaultsOf(alice).length, 1);
        assertEq(factory.agentVaults(botId).length, 1);
    }

    function test_ActWritesEconomicMemoryViaFactory() public {
        GuardedVault v = _create();
        vm.prank(botKey);
        v.act(venue, 1 ether, bytes32("open-pos"));

        assertEq(venue.balance, 1 ether);
        assertEq(mem.entryCount(), 1);
        EconomicMemory.Entry memory e = mem.getEntry(0);
        assertEq(e.agentId, botId);
        assertEq(e.tier, 1);
        assertEq(e.valueWei, 1 ether);
        assertEq(e.recorder, address(factory));
    }

    /// Vault palsu (bukan buatan factory) tidak bisa numpang nulis memory.
    function test_FakeVaultCannotRecord() public {
        vm.prank(mallory);
        vm.expectRevert(VaultFactory.NotAVault.selector);
        factory.recordAction(botId, 1 ether, bytes32("fake"));
    }

    function test_PolicyStillEnforced() public {
        GuardedVault v = _create();
        vm.startPrank(botKey);
        vm.expectRevert(GuardedVault.ExceedsMaxTx.selector);
        v.act(venue, 1 ether + 1, bytes32(0));
        vm.expectRevert(GuardedVault.TargetNotAllowed.selector);
        v.act(mallory, 0.5 ether, bytes32(0));
        // floor: saldo 5, floor 1, cap harian 2 → habiskan cap
        v.act(venue, 1 ether, bytes32(0));
        v.act(venue, 1 ether, bytes32(0));
        vm.expectRevert(GuardedVault.ExceedsDailyCap.selector);
        v.act(venue, 0.5 ether, bytes32(0));
        vm.stopPrank();
    }

    function test_OwnerControlsNotFactoryDeployer() public {
        GuardedVault v = _create();
        vm.prank(deployer); // deployer factory BUKAN owner vault
        vm.expectRevert(GuardedVault.NotOwner.selector);
        v.setTarget(mallory, true);
        vm.prank(alice);
        v.withdraw(1 ether);
        assertEq(alice.balance, 100 ether - 5 ether + 1 ether);
    }

    function testFuzz_FloorNeverBreached(uint96 x) public {
        GuardedVault v = _create();
        uint256 value = bound(x, 1, 1 ether);
        vm.prank(botKey);
        try v.act(venue, value, bytes32("fz")) {} catch {}
        assertGe(address(v).balance, 1 ether);
    }
}
