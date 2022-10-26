// SPDX-License-Identifier: MIT

import { ZeroUnderwriterLock } from "./35_140_ZeroUnderwriterLock.sol";

library ZeroUnderwriterLockBytecodeLib {
  function get() external pure returns (bytes memory result) {
    result = type(ZeroUnderwriterLock).creationCode;
  }
}