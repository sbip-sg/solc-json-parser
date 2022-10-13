//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage

pragma solidity ^0.7.0;

contract Branching {
    uint256 public count = 2**256-1000; 
    uint256 temp = 0;
    function add_overflow(uint256 input) public {
        if (input > 10000) {
            if (input % 10 == 0){    
                temp = 10; 
                if (input % 20 == 0 ){
                    temp = 20;
                    if (input % 50 == 0){
                        if (input %500 == 0)
                            count = count + input;
                    }
                }
            }
            else temp = 10;
        } else {
            temp = 4;
        }
    }
    function add_overflow_difficult(uint256 input) public {
        if (input > 10000) {
            if (input % 10 == 0){    
                temp = 10; 
                if (input % 20 == 0 ){
                    temp = 20;
                    if (input % 50 == 0)
                        if (input %500 == 0)
                            if (input %1000 == 0)
                                if (input %2000 == 0){
                                    count = 2**256-1000; 
                                    count = count + input;
                                }
                    
                }
            }
            else temp = 10;
        } else {
            temp = 4;
        }
    }
    function add_overflow_simple(uint256 input) public {
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
    function new_add_overflow(uint256 input, uint256 input2) public {
    	count = 2**256-100000;
        if (input > 10000) {
            if (input % 10 == 0){    
                temp = 10; 
                if (input2 % 20 > 7 ){
                    temp = 20;
                    count = count + input2 + input;
                }
            }
            else temp = 10;
        } else {
            temp = 4;
        }
    }
}
