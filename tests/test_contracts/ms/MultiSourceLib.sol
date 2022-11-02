// SPDX-License-Identifier: MIT

pragma solidity 0.7.0;

library MultiSourceLib{
    function unsafeAdd(uint32 x, uint32 y) public pure returns (uint32){
        return x + y;
    }
}


contract MultiSourceUtils{
    function unsafeAdd(uint32 x, uint32 y) public pure returns (uint32){
        return x + y;
    }
}
