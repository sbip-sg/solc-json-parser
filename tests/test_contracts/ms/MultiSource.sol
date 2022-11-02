// SPDX-License-Identifier: MIT

pragma solidity 0.7.0;

import {MultiSourceLib} from "./MultiSourceLib.sol";

contract MultiSource{
    using MultiSourceLib for uint32;
    constructor(){
    }

    function add(uint32 x, uint32 y) public pure returns (uint256){
        return x.unsafeAdd(y);
    }
    
}
