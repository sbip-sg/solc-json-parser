// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.2 <0.9.0;

contract Test {
    uint public x;
    // This function is called for all messages sent to
    // this contract (there is no other function).
    // Sending Ether to this contract will cause an exception,
    // because the fallback function does not have the `payable`
    // modifier.
    function deposit() public payable{
        
    }
    function withdraw () public{
        uint temp_ = block.timestamp;
        address payable sender = payable(msg.sender);
        sender.call(abi.encodeWithSignature("myFunction(uint)", 10));

    }
}

