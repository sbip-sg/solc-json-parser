// SPDX-License-Identifier: MIT

pragma solidity >=0.7.0 <0.8.0;
import { ICurvePool } from "./69_140_ICurvePool.sol";
import { IERC20 } from "./25_140_IERC20.sol";
import { ZeroCurveWrapper } from "./127_140_ZeroCurveWrapper.sol";
import { ICurveInt128 } from "./87_140_ICurveInt128.sol";
import { ICurveInt256 } from "./119_140_ICurveInt256.sol";
import { ICurveUInt128 } from "./118_140_ICurveUInt128.sol";
import { ICurveUInt256 } from "./104_140_ICurveUInt256.sol";
import { ICurveUnderlyingInt128 } from "./121_140_ICurveUnderlyingInt128.sol";
import { ICurveUnderlyingInt256 } from "./122_140_ICurveUnderlyingInt256.sol";
import { ICurveUnderlyingUInt128 } from "./120_140_ICurveUnderlyingUInt128.sol";
import { ICurveUnderlyingUInt256 } from "./115_140_ICurveUnderlyingUInt256.sol";
import { CurveLib } from "./117_140_CurveLib.sol";

contract ZeroCurveFactory {
  event CreateWrapper(address _wrapper);

  function createWrapper(
    bool _underlying,
    uint256 _tokenInIndex,
    uint256 _tokenOutIndex,
    address _pool
  ) public payable {
    emit CreateWrapper(address(new ZeroCurveWrapper(_tokenInIndex, _tokenOutIndex, _pool, _underlying)));
  }

  fallback() external payable {
    /* no op */
  }
}