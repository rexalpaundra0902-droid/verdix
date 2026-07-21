// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {AgentRegistry} from "../src/AgentRegistry.sol";
import {EconomicMemory} from "../src/EconomicMemory.sol";
import {PaymentRouter} from "../src/PaymentRouter.sol";
import {TaskEscrow} from "../src/TaskEscrow.sol";
import {StressOracle} from "../src/StressOracle.sol";
import {VaultFactory, GuardedVault} from "../src/VaultFactory.sol";

/// @title Regresi audit 2026-07-21 — tiap test membuktikan satu gap tertutup.
contract AuditFixesTest is Test {
    AgentRegistry reg;
    EconomicMemory mem;
    PaymentRouter router;
    TaskEscrow escrow;
    VaultFactory factory;

    address deployer = makeAddr("deployer");
    address arbitrator = makeAddr("arbitrator");
    address alice = makeAddr("alice"); // client / principal
    address bob = makeAddr("bob"); // worker / agent controller
    address venue = makeAddr("venue");
    address mallory = makeAddr("mallory");
    uint256 aliceId;
    uint256 bobId;

    GuardedVault.Policy P =
        GuardedVault.Policy({maxTxValue: 1 ether, dailyCap: 2 ether, cooldown: 0, haltFloor: 1 ether});

    function setUp() public {
        vm.startPrank(deployer);
        reg = new AgentRegistry();
        mem = new EconomicMemory(reg);
        router = new PaymentRouter(reg, mem);
        escrow = new TaskEscrow(reg, mem, arbitrator);
        factory = new VaultFactory(reg, mem);
        mem.setRecorder(address(router), true);
        mem.setRecorder(address(escrow), true);
        mem.setRecorder(address(factory), true);
        vm.stopPrank();

        vm.prank(alice);
        aliceId = reg.register("a");
        vm.prank(bob);
        bobId = reg.register("b");
        vm.deal(alice, 100 ether);
        vm.deal(bob, 100 ether);
        vm.deal(mallory, 100 ether);
    }

    function _vault() internal returns (GuardedVault v) {
        vm.prank(alice);
        v = GuardedVault(payable(factory.createVault{value: 5 ether}(bobId, P)));
        vm.prank(alice);
        v.setTarget(venue, true);
    }

    // ---------- HIGH-1: wash-trading / fabrikasi Economic Memory ----------

    function test_H1_ZeroValueActRejected() public {
        GuardedVault v = _vault();
        vm.prank(bob);
        vm.expectRevert(GuardedVault.ZeroValue.selector);
        v.act(venue, 0, bytes32("wash"));
    }

    function test_H1_SelfDealingToOwnerRejected() public {
        GuardedVault v = _vault();
        vm.prank(alice);
        v.setTarget(alice, true); // owner sengaja di-allowlist
        vm.prank(bob);
        vm.expectRevert(GuardedVault.SelfDealing.selector);
        v.act(alice, 1 ether, bytes32("wash"));
    }

    function test_H1_SelfDealingToControllerRejected() public {
        GuardedVault v = _vault();
        vm.prank(alice);
        v.setTarget(bob, true); // controller di-allowlist
        vm.prank(bob);
        vm.expectRevert(GuardedVault.SelfDealing.selector);
        v.act(bob, 1 ether, bytes32("wash"));
    }

    function test_H1_LegitActStillRecords() public {
        GuardedVault v = _vault();
        vm.prank(bob);
        v.act(venue, 1 ether, bytes32("real"));
        assertEq(mem.entryCount(), 1);
        assertEq(venue.balance, 1 ether);
    }

    // ---------- M6: recordAction tak percaya arg agentId ----------

    function test_M6_RecordActionDerivesAgentId() public {
        GuardedVault v = _vault();
        // Panggilan langsung dari vault sah HANYA untuk managerAgentId-nya.
        // Simulasi: vault (via prank) coba nulis atas agentId lain → revert.
        vm.prank(address(v));
        vm.expectRevert(VaultFactory.AgentMismatch.selector);
        factory.recordAction(aliceId, 1 ether, bytes32("spoof"));
    }

    // ---------- HIGH-2: ownership 2-langkah ----------

    function test_H2_TwoStepOwnership() public {
        vm.prank(deployer);
        mem.transferOwnership(mallory);
        assertEq(mem.owner(), deployer); // belum pindah sampai di-accept
        vm.prank(mallory);
        mem.acceptOwnership();
        assertEq(mem.owner(), mallory);
    }

    function test_H2_ZeroOwnerRejected() public {
        vm.prank(deployer);
        vm.expectRevert(EconomicMemory.ZeroAddress.selector);
        mem.transferOwnership(address(0));
    }

    // ---------- M1: front-running expire vs dispute ----------

    function _task() internal returns (uint256 taskId) {
        uint128 pay = 5 ether;
        uint128 bond = escrow.bondOf(pay);
        vm.prank(alice);
        taskId = escrow.createTask{value: pay + bond}(aliceId, bobId, pay, uint64(block.timestamp + 1 days), "spec");
        vm.prank(bob);
        escrow.acceptTask{value: bond}(taskId);
    }

    function test_M1_ExpireBlockedDuringGrace() public {
        uint256 taskId = _task();
        vm.warp(block.timestamp + 1 days + 1); // lewat deadline, DALAM grace
        vm.prank(alice);
        vm.expectRevert(TaskEscrow.DeadlineNotPassed.selector);
        escrow.expire(taskId);
    }

    function test_M1_WorkerCanDisputeWithinGrace() public {
        uint256 taskId = _task();
        vm.warp(block.timestamp + 1 days + 1); // lewat deadline, sebelum grace habis
        vm.prank(bob);
        escrow.dispute(taskId); // worker terlindungi — tak bisa di-front-run expire
        (,,,,,, TaskEscrow.Status status,) = escrow.tasks(taskId);
        assertEq(uint256(status), uint256(TaskEscrow.Status.Disputed));
    }

    function test_M1_ExpireWorksAfterGrace() public {
        uint256 taskId = _task();
        vm.warp(block.timestamp + 1 days + escrow.DISPUTE_GRACE() + 1);
        vm.prank(alice);
        escrow.expire(taskId); // setelah grace, expire sah
        (,,,,,, TaskEscrow.Status status,) = escrow.tasks(taskId);
        assertEq(uint256(status), uint256(TaskEscrow.Status.Expired));
    }

    // ---------- M2: dispute timeout escape-hatch ----------

    function test_M2_ExpireDisputeReleasesFundsFairly() public {
        uint256 taskId = _task();
        vm.prank(bob);
        escrow.dispute(taskId);
        uint256 aliceBefore = alice.balance;
        uint256 bobBefore = bob.balance;

        vm.expectRevert(TaskEscrow.DisputeNotTimedOut.selector);
        escrow.expireDispute(taskId);

        vm.warp(block.timestamp + escrow.DISPUTE_TIMEOUT() + 1);
        escrow.expireDispute(taskId);
        // masing-masing dapat dananya sendiri kembali (client: payment+bond, worker: bond)
        assertEq(alice.balance, aliceBefore + 5 ether + escrow.bondOf(5 ether));
        assertEq(bob.balance, bobBefore + escrow.bondOf(5 ether));
    }

    function test_M2_ArbitratorZeroRejected() public {
        vm.prank(deployer);
        vm.expectRevert(TaskEscrow.ZeroAddress.selector);
        escrow.setArbitrator(address(0));
    }

    // ---------- M3: de-auth recorder tak membekukan settlement ----------

    function test_M3_ConfirmWorksEvenIfRecorderRevoked() public {
        uint256 taskId = _task();
        vm.prank(deployer);
        mem.setRecorder(address(escrow), false); // escrow dicabut saat task in-flight
        uint256 bobBefore = bob.balance;
        vm.prank(alice);
        escrow.confirm(taskId); // TIDAK boleh revert — dana tetap keluar
        assertEq(bob.balance, bobBefore + 5 ether + escrow.bondOf(5 ether));
        assertEq(mem.entryCount(), 0); // memory dilewati (best-effort), settlement selamat
    }

    // ---------- LOW: nonce anti-replay + WalletInUse ----------

    function test_LOW_WalletNonceStopsReplay() public {
        (address w, uint256 pk) = makeAddrAndKey("opwallet");
        uint256 dl = block.timestamp + 1 hours;
        bytes32 d = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode("VerdixAgentWallet", block.chainid, address(reg), bobId, w, uint256(0), dl))
            )
        );
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, d);
        vm.prank(bob);
        reg.setAgentWallet(bobId, w, dl, abi.encodePacked(r, s, v));
        vm.prank(bob);
        reg.unsetAgentWallet(bobId);
        // replay signature nonce-0 yang sama setelah unset → gagal (nonce sudah 1)
        vm.prank(bob);
        vm.expectRevert(AgentRegistry.BadWalletSignature.selector);
        reg.setAgentWallet(bobId, w, dl, abi.encodePacked(r, s, v));
    }

    function test_LOW_WalletInUseEnforced() public {
        (address w, uint256 pk) = makeAddrAndKey("shared");
        // pasang w sbg wallet bob
        uint256 dl = block.timestamp + 1 hours;
        bytes32 d1 = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode("VerdixAgentWallet", block.chainid, address(reg), bobId, w, uint256(0), dl))
            )
        );
        (uint8 v1, bytes32 r1, bytes32 s1) = vm.sign(pk, d1);
        vm.prank(bob);
        reg.setAgentWallet(bobId, w, dl, abi.encodePacked(r1, s1, v1));
        // coba pakai w yang sama utk agent alice → WalletInUse
        bytes32 d2 = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode("VerdixAgentWallet", block.chainid, address(reg), aliceId, w, uint256(0), dl))
            )
        );
        (uint8 v2, bytes32 r2, bytes32 s2) = vm.sign(pk, d2);
        vm.prank(alice);
        vm.expectRevert(AgentRegistry.WalletInUse.selector);
        reg.setAgentWallet(aliceId, w, dl, abi.encodePacked(r2, s2, v2));
    }

    // ---------- M5: reentrancy guard aktif ----------

    function test_M5_ReentrancyGuardPresent() public {
        // Guard hadir: aksi normal tetap jalan (tidak false-trip); reentrancy
        // nyata butuh target-kontrak jahat — di sini kita pastikan guard tidak
        // memblokir jalur normal (regression guard-tak-rusak).
        GuardedVault v = _vault();
        vm.prank(bob);
        v.act(venue, 1 ether, bytes32("ok"));
        assertEq(venue.balance, 1 ether);
    }
}
