// SPDX-License-Identifier: MIT

pragma solidity >=0.4.23;

contract BugC{
    mapping (address => uint) credit;
    uint balance;
    
    function test4(address a) public {
        uint oCredit = credit[msg.sender];
        if (oCredit > 0) {
            balance -= oCredit;
            credit[msg.sender] = 0;
        }
    }

    function get_balance() public view returns (uint){
        return 100;
    }
}
    
