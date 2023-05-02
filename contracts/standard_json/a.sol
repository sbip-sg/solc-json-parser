// SPDX-License-Identifier: MIT

pragma solidity ^0.7.0;

abstract contract A {
    uint256 public count = 1;
    uint public time ;
    function add_overflow(uint256 input) public payable returns (uint256) {
        time = block.timestamp;
        count = (2**256 - 100);
        count = count + input;
        return count;
    }
    function test_payable(uint256 input ) public payable {
        require (msg.value == 10 ether);
        count = count + input;
    }
}
