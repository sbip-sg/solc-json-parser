// SPDX-License-Identifier: MIT
pragma solidity >=0.6.0;

import { BadgerBridgeZeroControllerMatic } from "./86_140_BadgerBridgeZeroControllerMatic.sol";
import { TransparentUpgradeableProxy } from "./82_140_TransparentUpgradeableProxy.sol";
import { ProxyAdmin } from "./81_140_ProxyAdmin.sol";

contract BadgerBridgeZeroControllerDeployer {
  address constant governance = 0x4A423AB37d70c00e8faA375fEcC4577e3b376aCa;
  event Deployment(address indexed proxy);

  constructor() {
    address logic = address(new BadgerBridgeZeroControllerMatic());
    ProxyAdmin proxy = new ProxyAdmin();
    ProxyAdmin(proxy).transferOwnership(governance);
    emit Deployment(
      address(
        new TransparentUpgradeableProxy(
          logic,
          address(proxy),
          abi.encodeWithSelector(BadgerBridgeZeroControllerMatic.initialize.selector, governance, governance)
        )
      )
    );
    selfdestruct(msg.sender);
  }
}