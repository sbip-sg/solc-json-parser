//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage

pragma solidity ^0.7.0;

contract Branching {
    uint256 public count = 2**256-1000; 
    uint256 temp = 0;

    function add_overflow(uint256 input) public {
        //654321
        if (input % 10 == 1)
            if (input % 100 == 21)
                if (input % 1000 == 321)
                    if (input % 10000 == 4321)
                        if (input % 100000 == 54321)
                            count = count + input;
                            
        
    }
}
