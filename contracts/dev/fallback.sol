// contracts/Fallback.sol
// SPDX-License-Identifier: Academic Free License v1.1

pragma solidity 0.7.0;

contract Fallback {
    receive() external payable{}
    function  receive() external payable{}
    function  fallback() external payable{}
    fallback() external{
        address payable to = payable(msg.sender);
        to.transfer(address(this).balance);
    }
}