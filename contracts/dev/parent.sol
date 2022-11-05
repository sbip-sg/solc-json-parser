// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

abstract contract BugC{
    mapping (address => uint) credit;
    uint balance;
    
    function test4(address a) public {
        uint oCredit = credit[msg.sender];
        if (oCredit > 0) {
            balance -= oCredit;
            (bool callResult, ) = msg.sender.call{value: oCredit}("");
            require (callResult);
            credit[msg.sender] = 0;
        }
    }

    function get_balance() public view returns (uint){
        return 100;
    }
}
    
