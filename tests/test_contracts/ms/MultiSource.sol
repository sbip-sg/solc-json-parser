// SPDX-License-Identifier: MIT

pragma solidity 0.7.0;

import {MultiSourceUtils} from "./MultiSourceLib.sol";

contract MultiSource{
    // using MultiSourceLib for uint32;
    uint256 i;
    MultiSourceUtils utils;
    constructor(){
        utils = new MultiSourceUtils();
    }

    function add(uint256 x, uint256 y) public returns (uint256){
        // i = x.unsafeAdd(y);
        i = utils.unsafeAdd(x, y);
        return i;
    }
    
}
