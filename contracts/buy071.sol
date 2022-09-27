pragma solidity 0.7.1;

contract Buy {
    mapping(address => uint256) public balances;

    address payable wallet;

    constructor(address payable _wallet) public {
        wallet = _wallet;
    }


    function buyToken() public payable {
        // buy a token
        balances[msg.sender] += 1;
        wallet.transfer(msg.value);
        // send ether to the wallet
    }
}