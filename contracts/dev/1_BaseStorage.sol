// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.17;
import * as Parent from "./parent.sol";
import {BaseStorage} from "./1_VirtualBaseStorage.sol";
// abstract contract BaseStorage {
//     uint256 some;
//     uint256 number;

//     function store(uint256 num) public {
//         number = num;
//     }

//     function retrieve() public view returns (uint256){
//         return number;
//     }
// }

contract Storage is BaseStorage, Parent.BugC {

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