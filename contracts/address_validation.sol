pragma solidity ^0.7.0;

contract Test {
    function test2(address a) internal returns (bool){
		require(a!=address(0));
		return true;
	}
	address admin;
	function test(address a) public{
		test2(a);
		admin = a;
	}
	function test3(address a) public {
		admin = a;
	}
}
