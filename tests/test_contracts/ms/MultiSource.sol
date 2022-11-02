// SPDX-License-Identifier: MIT

pragma solidity 0.7.0;

import {MultiSourceUtils} from "./MultiSourceLib.sol";

contract MultiSource{
    // using MultiSourceLib for uint32;
    uint32 i;
    MultiSourceUtils utils;
    constructor(){
        utils = new MultiSourceUtils();
    }

    function add(uint32 x, uint32 y) public returns (uint256){
        // i = x.unsafeAdd(y);
        i = utils.unsafeAdd(x, y);
        return i;
    }
    
}
