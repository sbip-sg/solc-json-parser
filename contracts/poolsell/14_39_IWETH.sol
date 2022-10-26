// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import { IERC20 } from './12_39_IERC20.sol';
import { IERC20Metadata } from './34_39_IERC20Metadata.sol';

/**
 * @title WETH (Wrapped ETH) interface
 */
interface IWETH is IERC20, IERC20Metadata {
    /**
     * @notice convert ETH to WETH
     */
    function deposit() external payable;

    /**
     * @notice convert WETH to ETH
     * @dev if caller is a contract, it should have a fallback or receive function
     * @param amount quantity of WETH to convert, denominated in wei
     */
    function withdraw(uint256 amount) external;
}