// SPDX-License-Identifier: MIT

pragma solidity 0.7.0;

library MultiSourceLib{
    function unsafeAdd(uint256 x, uint256 y) public pure returns (uint256){
        return x + y;
    }
}


contract MultiSourceUtils{
    uint256 d;
    function unsafeAdd(uint256 x, uint256 y) public returns (uint256){
        d = x + y;
        return d;
    }
}
