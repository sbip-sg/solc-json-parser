pragma solidity >=0.4.23;

abstract contract BaseStorage {
    uint256 some;
    uint256 number;

    function store(uint256 num) public {
        number = num;
    }

    function retrieve() public view returns (uint256){
        return number;
    }
}