pragma solidity ^0.8.0;

contract MockLinkToken{
    function balanceOf(address owner) external pure returns (uint256 balance){
        return 2**100;
    }
    function decimals() external pure returns (uint8 decimalPlaces){
         return 18;
    } 
    function transfer(address to, uint256 value) external returns (bool success){
        return true;
    }
}
abstract contract VRFConsumerBase {
    MockLinkToken LINK;
    address private immutable vrfCoordinator;
    constructor(address _vrfCoordinator, address _link) {
        vrfCoordinator = _vrfCoordinator;
        LINK = new MockLinkToken();
    }
    function fulfillRandomness(bytes32 requestId, uint256 randomness) internal virtual;
    function requestRandomness(bytes32 _keyHash, uint256 _fee) internal returns (bytes32 requestId) {
        bytes32 sampleID = "sampleID";
        fulfillRandomness(sampleID, uint256(blockhash(block.number-1)));
        return sampleID;
    }
}