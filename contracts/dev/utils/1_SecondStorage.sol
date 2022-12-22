pragma solidity >=0.4.23;

abstract contract SecondStorage {
    uint256 number_sec;

    function store_sec(uint256 num) public {
        number_sec = num;
    }

    function retrieve_sec() public view returns (uint256){
        return number_sec;
    }
}