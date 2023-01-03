// SPDX-License-Identifier: MIT
pragma solidity 0.7.6;
pragma experimental ABIEncoderV2;

contract Test {
  struct Sig { uint8 v; bytes32 r; bytes32 s;}

  function claim(bytes32 _msg, Sig memory sig) public {
    address signer = ecrecover(_msg, sig.v, sig.r, sig.s);
    // require(signer == owner);
    payable(msg.sender).transfer(address(this).balance);
  }

  function vec_add(uint[2] memory a, uint[2] memory b) public returns (uint[2] memory c){
    c[0] = a[0] + b[0]; //overflow
    c[1] = a[1] + b[1]; //overflow
  }
}
