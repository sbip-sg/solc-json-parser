pragma solidity ^0.7.0;
contract example{
    function always_fail() public {
        revert();
    }
    function always_success() public{
        // do nothing
    }
    function test_call_failed() public{
        (bool success, bytes memory result)  = address(this).call(hex"31ffb467");
        require (success);
    }
    function test_call_success() public{
        address(this).call(hex"bcf95ac1");
    }
    function test_call_success_success_failed() public{
        address(this).call(hex"60193614");
    }
}