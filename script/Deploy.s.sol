// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {AgentRegistry} from "../src/AgentRegistry.sol";
import {EconomicMemory} from "../src/EconomicMemory.sol";
import {PaymentRouter} from "../src/PaymentRouter.sol";
import {TaskEscrow} from "../src/TaskEscrow.sol";
import {StressOracle} from "../src/StressOracle.sol";

/// Deploy seluruh stack Verdix Phase 1. Deployer = owner + arbitrator + attestor
/// (MVP; di testnet/mainnet nanti dipisah per role).
contract Deploy is Script {
    function run() external {
        vm.startBroadcast();
        AgentRegistry registry = new AgentRegistry();
        EconomicMemory mem = new EconomicMemory(registry);
        PaymentRouter router = new PaymentRouter(registry, mem);
        TaskEscrow escrow = new TaskEscrow(registry, mem, msg.sender);
        StressOracle oracle = new StressOracle(registry, mem);
        mem.setRecorder(address(router), true);
        mem.setRecorder(address(escrow), true);
        mem.setRecorder(address(oracle), true);
        oracle.setAttestor(msg.sender, true);
        vm.stopBroadcast();

        console.log("AgentRegistry :", address(registry));
        console.log("EconomicMemory:", address(mem));
        console.log("PaymentRouter :", address(router));
        console.log("TaskEscrow    :", address(escrow));
        console.log("StressOracle  :", address(oracle));
    }
}
