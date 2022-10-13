pragma solidity ^0.6.1;

contract RevertContract {
    uint256 level = 0;

    function testRevert(uint256 x) public returns(uint256){
        require(x < 1000, "REQUIRE: Input valuee is too large");
        level += 1;
        return x + 108928293 - level;
    }


    function testAssert(uint256 x) public returns(uint256){
        assert(x < 500);
        level += 1;
        return x + 8928293 - level;
    }

}
