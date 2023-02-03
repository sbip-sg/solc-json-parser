pragma solidity 0.8.0;
contract Test {
    int a;
    mapping (address => bool) test;
    receive() external payable{

}
    function bug(address[10] memory input) public {
        for(uint i=0; i<input.length; i++){
            test[input[i]] = true;
        }
        //bug is hidden if we dont control input length
        uint temp = block.timestamp;
        temp = block.number;
        payable(msg.sender).transfer(1234);
    }
 }
