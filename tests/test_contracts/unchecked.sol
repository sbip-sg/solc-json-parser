pragma solidity 0.8.18;
interface TestI {
    function foo () external ;
}

contract Test{

    function test_bug(address input) public{
        input.call("abC");
    }

}

contract Revert{
    fallback() external {
        revert();
    }
}

contract Test2{
    function test_1(TestI input) public {
        input.foo();
    }
    function test_2(address input) public returns (bool func_res){
        (bool success, bytes memory result ) = input.call("abcd");

        if (success)
            func_res = true;
        else
            func_res = false;
    }
    function test_3(address input) public returns (bool func_res){
        (bool success, bytes memory result ) = input.call("abcd");

        return success;
    }
    function test_4(address input) public {
        input.call("abcd");
    }
    function test_5(TestI input) public returns (bool result){
        try input.foo() {
            result = true;
        }catch {
            result = false;
        }
    }
}
