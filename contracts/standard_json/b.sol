// SPDX-License-Identifier: MIT

pragma solidity ^0.7.0;

abstract contract B{
    function deposit() public payable{

    }
    function withdraw () public{
        uint temp_ = block.timestamp;
        address payable sender = payable(msg.sender);
        sender.call(abi.encodeWithSignature("myFunction(uint)", 10));

    }
}
