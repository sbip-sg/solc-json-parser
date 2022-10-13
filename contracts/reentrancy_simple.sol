pragma solidity ^0.7.0;
 contract Reentrance {
    mapping (address => uint) balances;
    uint public level  = 100;

    function deposit () public payable{
        level++;
    }

    function withdraw(uint _amount) public {
        if (_amount > level){
            // level = (2**256 - 100) + level;
            (bool result,) = msg.sender.call{value:_amount}("");
            require(result);
        }
    }

 }

