//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage

pragma solidity ^0.7.0;

contract Branching {
    uint256 public count = 2**256-1000; 
    uint256 temp = 0;

    function add_overflow(uint256 input) public {
        //0 
        if (input > 54321){
                count = 2**256-1000;                 
                count = count + input;
        }

    }
    function add_overflow_2(uint256 input, uint input2) public {
        //12345
        if (input > 12345){
            count = 2**256-1000; 
            count = count + input;
        }
                            
        
    }
    function add_overflow_3(uint256 input, uint input2) public {
        //12345
        if (input2 % 1234 == 0){
            count = 2**256-1000; 
            count = count + input;
        }
                            
        
    }
}
