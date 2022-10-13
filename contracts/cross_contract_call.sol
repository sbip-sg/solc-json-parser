
pragma solidity >=0.7.0 <0.9.0;

/**
 * @title Storage
 * @dev Store & retrieve value in a variable
 */
contract Storage {

    uint256 number;

    /**
     * @dev Store value in variable
     * @param num value to store
     */
    function store(uint256 num) public {
        number = num;
        // require(false);
    }

    /**
     * @dev Return value 
     * @return value of 'number'
     */
    function retrieve() public view returns (uint256){
        return number;
    }
}

contract Attacker {

    uint256 number;


    function call(address addr) public {
        (bool success,) = address(addr).call(abi.encodeWithSignature("store(uint256)", 1234));
        //a.store(1);
    }

}