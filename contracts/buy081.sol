pragma solidity 0.8.1;

contract Buy {
    mapping(address => uint256) public balances;

    address payable wallet;
    address owner;
    constructor(address payable _wallet) public {
        wallet = _wallet;
    }

    modifier onlyOwner() {
        require (msg.sender == owner);
        _;
    }

    modifier onlyWhileOpen() {
        require(block.timestamp >= 0);
        _;
    }
    function buyToken(string memory _str1, uint8 _int2) public payable onlyOwner onlyWhileOpen returns (uint8) {
        // buy a token
        balances[msg.sender] += 1;
        wallet.transfer(msg.value);
        // send ether to the wallet
        return _int2;
    }
}