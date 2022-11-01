// contracts/Fallback.sol
// SPDX-License-Identifier: Academic Free License v1.1

pragma solidity ^0.5.0;

contract Fallback {

    function() external {x=1;}
    function receive() external payable  {}
    function fallback() external payable {}
    uint x;

}