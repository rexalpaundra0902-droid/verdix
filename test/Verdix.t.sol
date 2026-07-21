// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {AgentRegistry} from "../src/AgentRegistry.sol";
import {EconomicMemory} from "../src/EconomicMemory.sol";
import {PaymentRouter} from "../src/PaymentRouter.sol";
import {TaskEscrow} from "../src/TaskEscrow.sol";
import {StressOracle} from "../src/StressOracle.sol";

contract VerdixTest is Test {
    AgentRegistry reg;
    EconomicMemory mem;
    PaymentRouter router;
    TaskEscrow escrow;
    StressOracle oracle;

    address deployer = makeAddr("deployer");
    address arbitrator = makeAddr("arbitrator");
    address alice = makeAddr("alice"); // client agent
    address bob = makeAddr("bob"); // worker agent
    address mallory = makeAddr("mallory"); // attacker
    uint256 aliceId;
    uint256 bobId;
    uint256 malloryId;

    function setUp() public {
        vm.startPrank(deployer);
        reg = new AgentRegistry();
        mem = new EconomicMemory(reg);
        router = new PaymentRouter(reg, mem);
        escrow = new TaskEscrow(reg, mem, arbitrator);
        oracle = new StressOracle(reg, mem);
        mem.setRecorder(address(router), true);
        mem.setRecorder(address(escrow), true);
        mem.setRecorder(address(oracle), true);
        oracle.setAttestor(deployer, true);
        vm.stopPrank();

        vm.prank(alice);
        aliceId = reg.register("https://alice.agents.verdix.io/agent.json");
        vm.prank(bob);
        bobId = reg.register("https://bob.agents.verdix.io/agent.json");
        vm.prank(mallory);
        malloryId = reg.register("https://mallory.agents.verdix.io/agent.json");

        vm.deal(alice, 100 ether);
        vm.deal(bob, 100 ether);
        vm.deal(mallory, 100 ether);
    }

    // ---------- Registry (ERC-8004 surface) ----------

    function test_RegisterMintsNftAndSetsUri() public view {
        assertEq(reg.agentCount(), 3);
        assertEq(reg.ownerOf(aliceId), alice);
        assertEq(reg.controllerOf(bobId), bob);
        assertEq(reg.tokenURI(aliceId), "https://alice.agents.verdix.io/agent.json");
    }

    function test_MetadataSetGet() public {
        vm.prank(alice);
        reg.setMetadata(aliceId, "agentDomain", bytes("alice.agent"));
        assertEq(reg.getMetadata(aliceId, "agentDomain"), bytes("alice.agent"));

        vm.prank(mallory);
        vm.expectRevert(AgentRegistry.NotAgentOwner.selector);
        reg.setMetadata(aliceId, "agentDomain", bytes("pwned"));
    }

    function test_SetAgentUriOnlyOwner() public {
        vm.prank(mallory);
        vm.expectRevert(AgentRegistry.NotAgentOwner.selector);
        reg.setAgentURI(aliceId, "https://stolen/agent.json");
    }

    function test_SetAgentWalletRequiresConsentSignature() public {
        (address wallet, uint256 walletPk) = makeAddrAndKey("botwallet");
        uint256 deadline = block.timestamp + 1 hours;
        bytes32 digest = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode("VerdixAgentWallet", block.chainid, address(reg), bobId, wallet, reg.walletNonce(bobId), deadline))
            )
        );
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(walletPk, digest);

        // signature valid → wallet terpasang, kontrol pindah tercatat
        vm.prank(bob);
        reg.setAgentWallet(bobId, wallet, deadline, abi.encodePacked(r, s, v));
        assertEq(reg.controllerOf(bobId), wallet);
        assertEq(reg.controlChangesOf(bobId).length, 1);

        // signature dari key lain → revert (tidak bisa menunjuk wallet orang)
        (, uint256 otherPk) = makeAddrAndKey("other");
        (v, r, s) = vm.sign(otherPk, digest);
        vm.prank(bob);
        vm.expectRevert(AgentRegistry.BadWalletSignature.selector);
        reg.setAgentWallet(bobId, wallet, deadline, abi.encodePacked(r, s, v));
    }

    /// Lubang "beli reputasi": transfer NFT agent HARUS tercatat sebagai
    /// perpindahan kontrol dan wallet operasional lama dicabut.
    function test_TransferLogsControlChangeAndClearsWallet() public {
        (address wallet, uint256 walletPk) = makeAddrAndKey("botwallet");
        uint256 deadline = block.timestamp + 1 hours;
        bytes32 digest = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode("VerdixAgentWallet", block.chainid, address(reg), bobId, wallet, reg.walletNonce(bobId), deadline))
            )
        );
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(walletPk, digest);
        vm.prank(bob);
        reg.setAgentWallet(bobId, wallet, deadline, abi.encodePacked(r, s, v));

        vm.prank(bob);
        reg.transferFrom(bob, mallory, bobId);

        // kontrol = owner baru, wallet lama TIDAK diwarisi
        assertEq(reg.controllerOf(bobId), mallory);
        // dua control change: wallet_set + ownership_transfer → scorer akan decay
        assertEq(reg.controlChangesOf(bobId).length, 2);
    }

    // ---------- Economic Memory admission ----------

    function test_SelfReportCannotWriteMemory() public {
        vm.prank(mallory);
        vm.expectRevert(EconomicMemory.NotRecorder.selector);
        mem.record(
            malloryId, 0, EconomicMemory.ActionClass.Agreement, 2, 1 ether, EconomicMemory.Outcome.Success, bytes32(0)
        );
    }

    function test_UnauthorizedRecorderContractReverts() public {
        vm.startPrank(mallory);
        PaymentRouter fake = new PaymentRouter(reg, mem);
        vm.expectRevert(EconomicMemory.NotRecorder.selector);
        fake.pay{value: 1 ether}(malloryId, bobId, bytes32("fake"));
        vm.stopPrank();
    }

    function test_OnlyOwnerSetsRecorder() public {
        vm.prank(mallory);
        vm.expectRevert(EconomicMemory.NotOwner.selector);
        mem.setRecorder(mallory, true);
    }

    // ---------- Tier 1: PaymentRouter ----------

    function test_PaymentWritesTier1Entry() public {
        vm.prank(alice);
        router.pay{value: 2 ether}(aliceId, bobId, bytes32("invoice-1"));

        assertEq(mem.entryCount(), 1);
        EconomicMemory.Entry memory e = mem.getEntry(0);
        assertEq(e.agentId, aliceId);
        assertEq(e.counterpartyId, bobId);
        assertEq(uint8(e.actionClass), uint8(EconomicMemory.ActionClass.Settlement));
        assertEq(e.tier, 1);
        assertEq(e.valueWei, 2 ether);
        assertEq(bob.balance, 102 ether);
        assertEq(mem.entryIdsOf(aliceId).length, 1);
        assertEq(mem.entryIdsOf(bobId).length, 1);
    }

    function test_PayRequiresControllerKey() public {
        vm.prank(mallory);
        vm.expectRevert(PaymentRouter.NotAgentOwner.selector);
        router.pay{value: 1 ether}(aliceId, bobId, bytes32(0));
    }

    // ---------- Tier 2: TaskEscrow happy path ----------

    function _openAndAccept(uint128 payment) internal returns (uint256 taskId) {
        uint128 bond = escrow.bondOf(payment);
        vm.prank(alice);
        taskId = escrow.createTask{value: payment + bond}(
            aliceId, bobId, payment, uint64(block.timestamp + 1 days), bytes32("spec")
        );
        vm.prank(bob);
        escrow.acceptTask{value: bond}(taskId);
    }

    function test_EscrowConfirmPaysAndRecords() public {
        uint256 bobBefore = bob.balance;
        uint256 aliceBefore = alice.balance;
        uint256 taskId = _openAndAccept(10 ether);

        vm.prank(alice);
        escrow.confirm(taskId);

        assertEq(bob.balance, bobBefore + 10 ether);
        assertEq(alice.balance, aliceBefore - 10 ether);

        assertEq(mem.entryCount(), 2);
        EconomicMemory.Entry memory w = mem.getEntry(0);
        assertEq(w.agentId, bobId);
        assertEq(w.tier, 2);
        assertEq(uint8(w.actionClass), uint8(EconomicMemory.ActionClass.Agreement));
        assertEq(uint8(w.outcome), uint8(EconomicMemory.Outcome.Success));
        EconomicMemory.Entry memory c = mem.getEntry(1);
        assertEq(c.agentId, aliceId);
        assertEq(c.tier, 1);
    }

    function test_FarmingRequiresRealCapitalLock() public {
        uint128 payment = 10 ether;
        uint128 bond = escrow.bondOf(payment);
        assertEq(bond, 1 ether);

        vm.prank(mallory);
        uint256 taskId = escrow.createTask{value: payment + bond}(
            malloryId, bobId, payment, uint64(block.timestamp + 1 days), bytes32("farm")
        );
        vm.prank(mallory);
        vm.expectRevert(TaskEscrow.BadStatus.selector);
        escrow.confirm(taskId);

        vm.prank(bob);
        escrow.acceptTask{value: bond}(taskId);
        vm.prank(mallory);
        escrow.confirm(taskId);
        assertEq(mem.entryCount(), 2);
    }

    // ---------- Tier 3: dispute ----------

    function test_DisputeWorkerWinsTakesClientBond() public {
        uint256 taskId = _openAndAccept(10 ether);
        uint256 bobBefore = bob.balance;

        vm.prank(bob);
        escrow.dispute(taskId);
        vm.prank(arbitrator);
        escrow.rule(taskId, true);

        assertEq(bob.balance, bobBefore + 12 ether);
        EconomicMemory.Entry memory e = mem.getEntry(0);
        assertEq(e.tier, 3);
        assertEq(uint8(e.outcome), uint8(EconomicMemory.Outcome.DisputedFor));
    }

    function test_DisputeWorkerLosesRecordedAgainst() public {
        uint256 taskId = _openAndAccept(10 ether);
        uint256 aliceBefore = alice.balance;

        vm.prank(alice);
        escrow.dispute(taskId);
        vm.prank(arbitrator);
        escrow.rule(taskId, false);

        assertEq(alice.balance, aliceBefore + 12 ether);
        assertEq(uint8(mem.getEntry(0).outcome), uint8(EconomicMemory.Outcome.DisputedAgainst));
    }

    function test_OnlyArbitratorRules() public {
        uint256 taskId = _openAndAccept(1 ether);
        vm.prank(bob);
        escrow.dispute(taskId);
        vm.prank(mallory);
        vm.expectRevert(TaskEscrow.NotArbitrator.selector);
        escrow.rule(taskId, true);
    }

    // ---------- Expiry = verified failure ----------

    function test_ExpiryRecordsWorkerFailure() public {
        uint256 taskId = _openAndAccept(10 ether);
        vm.warp(block.timestamp + 2 days);
        escrow.expire(taskId);

        EconomicMemory.Entry memory e = mem.getEntry(0);
        assertEq(e.agentId, bobId);
        assertEq(uint8(e.outcome), uint8(EconomicMemory.Outcome.Failed));
        assertEq(e.tier, 2);
    }

    function test_ExpireBeforeDeadlineReverts() public {
        uint256 taskId = _openAndAccept(1 ether);
        vm.expectRevert(TaskEscrow.DeadlineNotPassed.selector);
        escrow.expire(taskId);
    }

    function test_CancelOpenTaskNoEntry() public {
        vm.prank(alice);
        uint256 taskId =
            escrow.createTask{value: 11 ether}(aliceId, bobId, 10 ether, uint64(block.timestamp + 1 days), bytes32(0));
        vm.prank(alice);
        escrow.cancel(taskId);
        assertEq(mem.entryCount(), 0);
    }

    // ---------- Tier 4: StressOracle ----------

    function test_StressAttestOnlyAttestor() public {
        vm.prank(mallory);
        vm.expectRevert(StressOracle.NotAttestor.selector);
        oracle.attest(malloryId, 1 ether, true, bytes32("pump"));

        vm.prank(deployer);
        oracle.attest(bobId, 3 ether, false, bytes32("liq"));
        EconomicMemory.Entry memory e = mem.getEntry(0);
        assertEq(e.tier, 4);
        assertEq(uint8(e.actionClass), uint8(EconomicMemory.ActionClass.Stress));
        assertEq(uint8(e.outcome), uint8(EconomicMemory.Outcome.Failed));
    }

    // ---------- Escrow tetap jalan dengan operational wallet ----------

    function test_EscrowWithOperationalWallet() public {
        (address wallet, uint256 walletPk) = makeAddrAndKey("botwallet");
        vm.deal(wallet, 10 ether);
        uint256 deadline = block.timestamp + 1 hours;
        bytes32 digest = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode("VerdixAgentWallet", block.chainid, address(reg), bobId, wallet, reg.walletNonce(bobId), deadline))
            )
        );
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(walletPk, digest);
        vm.prank(bob);
        reg.setAgentWallet(bobId, wallet, deadline, abi.encodePacked(r, s, v));

        uint128 payment = 5 ether;
        uint128 bond = escrow.bondOf(payment);
        vm.prank(alice);
        uint256 taskId = escrow.createTask{value: payment + bond}(
            aliceId, bobId, payment, uint64(block.timestamp + 1 days), bytes32("spec")
        );
        // owner asli (bob) BUKAN controller lagi → tidak bisa accept
        vm.prank(bob);
        vm.expectRevert(TaskEscrow.NotAgentOwner.selector);
        escrow.acceptTask{value: bond}(taskId);
        // wallet operasional yang accept + menerima payout
        vm.prank(wallet);
        escrow.acceptTask{value: bond}(taskId);
        vm.prank(alice);
        escrow.confirm(taskId);
        assertEq(wallet.balance, 10 ether - bond + bond + payment);
    }

    // ---------- Fuzz ----------

    function testFuzz_BondAlwaysTenPercent(uint128 payment) public view {
        payment = uint128(bound(payment, 1, type(uint112).max));
        assertEq(escrow.bondOf(payment), (uint256(payment) * 1000) / 10_000);
    }

    function testFuzz_EscrowConservesEther(uint96 payment96) public {
        uint128 payment = uint128(bound(payment96, 1 gwei, 50 ether));
        uint256 total = alice.balance + bob.balance;
        uint256 taskId = _openAndAccept(payment);
        vm.prank(alice);
        escrow.confirm(taskId);
        assertEq(alice.balance + bob.balance, total);
        assertEq(address(escrow).balance, 0);
    }
}
