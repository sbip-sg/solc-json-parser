// SPDX-License-Identifier: MIT

pragma solidity 0.7.0;

import "./a.sol";
import "./b.sol";

contract Main is A, B{
    A a;
    function proxy_add(uint256 i) public payable returns (uint256) {
        return add_overflow(i);
    }
}
