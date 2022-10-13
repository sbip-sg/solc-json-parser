
//Multi-transactional, multi-function
//Arithmetic instruction reachable

pragma solidity ^0.7.0;

contract IntegerOverflowMultiTxMultiFuncFeasible {
    uint256 private initialized = 0;
    uint256 private initialized_2 = 0;
    uint256 private initialized_3 = 0;
    uint256 public count = 1;
    uint256 public lock = 0;

    function init(uint a) public {
        initialized = a;
    }
    function init2(uint b) public {
        initialized_2 = b;
    }
    function init3(uint c) public {
        initialized_3 = c;
    }
    function run(uint256 input) public {
        if (initialized + initialized_2 != 1234)
            return;
        count -= input;
    }
    // function add_overflow_2(uint256 input, uint input2) public {
    //     //12345
    //     if (input > 12345){
    //         count = 2**256-1000; 
    //         count = count + input;
    //     }
                            
    
    // }
}
