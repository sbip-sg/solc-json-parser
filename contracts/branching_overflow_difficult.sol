//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage

pragma solidity ^0.7.0;

contract Branching {
    uint256 public count = 2**256-1000; 
    uint256 temp = 0;

    function add_overflow(uint256 input) public {
        //0 
        if (input == 654321){
                                
                count = count + input;
        }

    }
}
