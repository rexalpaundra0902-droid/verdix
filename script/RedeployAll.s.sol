// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {AgentRegistry} from "../src/AgentRegistry.sol";
import {EconomicMemory} from "../src/EconomicMemory.sol";
import {PaymentRouter} from "../src/PaymentRouter.sol";
import {TaskEscrow} from "../src/TaskEscrow.sol";
import {StressOracle} from "../src/StressOracle.sol";
import {VaultFactory} from "../src/VaultFactory.sol";
import {RiskGuardVault} from "../src/RiskGuardVault.sol";
import {VDX} from "../src/VDX.sol";
import {VDXStaking} from "../src/VDXStaking.sol";

/// Redeploy penuh stack Verdix (9 kontrak) DENGAN fix audit 2026-07-21, ke BSC
/// testnet, satu broadcast (hindari nonce-race RPC publik). Deployer = owner +
/// arbitrator + attestor + controller kedua agent demo (MVP re-seed).
/// Storage vars dipakai supaya tidak "stack too deep" (banyak kontrak).
contract RedeployAll is Script {
    AgentRegistry reg;
    EconomicMemory mem;
    PaymentRouter router;
    TaskEscrow escrow;
    StressOracle oracle;
    VaultFactory factory;
    VDX vdx;
    VDXStaking staking;
    RiskGuardVault vault;
    uint256 botId;
    uint256 rekuId;

    function run() external {
        uint256 pk = vm.envUint("DEPLOYER_PK");
        address me = vm.addr(pk);

        vm.startBroadcast(pk);
        _deployAndWire(me);
        _seed();
        vm.stopBroadcast();

        console.log("AgentRegistry :", address(reg));
        console.log("EconomicMemory:", address(mem));
        console.log("PaymentRouter :", address(router));
        console.log("TaskEscrow    :", address(escrow));
        console.log("StressOracle  :", address(oracle));
        console.log("VaultFactory  :", address(factory));
        console.log("VDX           :", address(vdx));
        console.log("VDXStaking    :", address(staking));
        console.log("RiskGuardVault:", address(vault));
        console.log("botId         :", botId);
        console.log("rekuId        :", rekuId);
    }

    function _deployAndWire(address me) internal {
        reg = new AgentRegistry();
        mem = new EconomicMemory(reg);
        router = new PaymentRouter(reg, mem);
        escrow = new TaskEscrow(reg, mem, me);
        oracle = new StressOracle(reg, mem);
        factory = new VaultFactory(reg, mem);
        vdx = new VDX(me);
        staking = new VDXStaking(vdx, reg);
        mem.setRecorder(address(router), true);
        mem.setRecorder(address(escrow), true);
        mem.setRecorder(address(oracle), true);
        mem.setRecorder(address(factory), true);
        oracle.setAttestor(me, true);

        botId = reg.register("https://smc-bot.agents.verdix.io/agent.json");
        rekuId = reg.register("https://reku.agents.verdix.io/agent.json");

        vault = new RiskGuardVault(
            reg,
            mem,
            botId,
            RiskGuardVault.Policy({maxTxValue: 0.005 ether, dailyCap: 0.01 ether, cooldown: 30, haltFloor: 0.02 ether})
        );
        mem.setRecorder(address(vault), true);
        (bool funded,) = address(vault).call{value: 0.03 ether}(""); // deposit via receive()
        require(funded, "fund vault");
    }

    function _seed() internal {
        // Re-audit 2026-07-21: seed pakai SATU controller (deployer) utk dua agent.
        // Escrow & payment SENGAJA tak di-seed di sini — fix H-A/H-B kini menolak
        // settlement/task antar-agent yang controllernya SAMA (anti wash), jadi
        // demo dua-tier itu butuh 2 key operator beda (di-seed manual / bootstrap).
        // Jalur yang sah single-controller: aksi vault (target venue independen)
        // + stress attest. Escrow/payment tetap tercakup 63 forge test.

        // aksi vault compliant (value>0, target venue != owner/controller/self) — HIGH-1 + M-1 aktif
        address venue = address(uint160(uint256(keccak256("verdix-demo-venue"))));
        vault.setTarget(venue, true);
        vault.act(venue, 0.004 ether, keccak256("open-pos"));

        // stress attest Tier4
        oracle.attest(botId, 0.01 ether, true, keccak256("drawdown-recovered"));
        oracle.attest(botId, 0.02 ether, true, keccak256("sl-disciplined"));
    }
}
