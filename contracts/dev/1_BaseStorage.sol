// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0;
import * as Parent from "../parent/parent.sol";
//import * as Parent from "./parent.sol";
import {BaseStorage} from "./1_VirtualBaseStorage.sol";
import {SecondStorage} from "./utils/1_SecondStorage.sol";

contract Storage is BaseStorage, SecondStorage, Parent.BugC {

    function add_store(uint256 num) public {
        store(num + 1);
    }

    function retrieve_double() public view returns (uint256){
        return retrieve() * 2;
    }

    function check_balance() public view returns (uint256){
        return get_balance() + 1;
    }
}