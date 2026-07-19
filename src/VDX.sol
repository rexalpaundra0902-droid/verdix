// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "openzeppelin-contracts/contracts/token/ERC20/ERC20.sol";
import {ERC20Burnable} from "openzeppelin-contracts/contracts/token/ERC20/extensions/ERC20Burnable.sol";

/// @title VDX — token utilitas protokol Verdix (TESTNET)
/// @notice Supply 500.000.000, fixed selamanya — tidak ada mint tambahan
///         (spec v8). Utility Phase 1 yang sudah hidup: stake-to-register via
///         VDXStaking (skin in the game per agent, dibaca Trust Intelligence).
///         Fee model per tier & governance menyusul saat ada pemakaian nyata.
contract VDX is ERC20, ERC20Burnable {
    uint256 public constant TOTAL_SUPPLY = 500_000_000e18;

    constructor(address treasury) ERC20("Verdix", "VDX") {
        _mint(treasury, TOTAL_SUPPLY);
    }
}
