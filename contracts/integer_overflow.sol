//Single transaction overflow
//Post-transaction effect: overflow escapes to publicly-readable storage
pragma solidity ^0.7.0;

contract IntegerOverflowAdd {
    uint256 public count = 1;
    uint public time ;
    function add_overflow(uint256 input) public payable returns (uint256) {
        time = block.timestamp;
        count = (2**256 - 100);
        count = count + input;
        return count;
    }
    function test_payable(uint256 input ) public payable {
        require (msg.value == 10 ether);
        count = count + input;
    }
    fallback ()  external{
        revert();
    }
}
