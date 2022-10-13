//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage

pragma solidity ^0.7.0;

contract Branching {
    uint256 public count = 2**256-1000; 
    uint256 temp = 0;
    function add_overflow(uint256 input) public {
        // solution 642
        if (input > 100) {
            input = input - 100;
            if ( input > 500 && input % 10 == 2){    
                input = input - 500;
                temp = 10; 
                if (input % 20 > 1 ){
                    temp = 20;
                    if (2*input > 60)
                        if (input - 42 < 5)
                                if (input %42 == 0){
                                    count = 2**256-100; 
                                    count = count + input;
                                }
                }
            }
            else temp = 10;
        } else {
            temp = 4;
        }
    } 
}
