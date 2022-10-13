//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage

pragma solidity ^0.7.0;

contract Branching {
    int256 public count = 0;

    function run(int32 input) public {

// Auto generated code
emit OurDebug("run");
        if (input > 10) {
            if (input > 20) 
                count = 20;
            else count = 10;
        } else {
            if (input < 3) {
                count = 3;
                if (input <0){
                    count = 0;
                    if (input < -10)
                        count = -10;
                } 
                
            } else count = 4;
        }
    }

// Auto generated code
event OurDebug(string);
}
