pragma solidity ^0.7.0;

contract IntegerOverflowAdd {
	uint global_state = 2**256-100;
	function test(uint a, uint[12] memory b , bytes8 c, bytes memory d, bytes8[3] memory de, address[2] memory gh ) public{
		global_state = global_state + 2000;
	}
}
