pragma solidity ^0.7.0;

contract Test{
    uint256 public a = 123333;
//    string public  b = unicode"Hello 😃"; // work only above 0.7.0
    bool public    c = true;
    string public  d = "Hello";
    string public  e = "ac43fe";
//    bytes          foo = hex"00112233" hex"44556677"; // work only above 0.6.0
    address public f = 0x1234567890123456789012345678901234567890;
    string public  g = '123';

    uint256 public aa = 0;
    uint256 public ab = 0;

    int256 public ba = 0;
    int256 public bc = 0;

    bytes public  ca = hex"11";
    bytes1 public cb = 0x11;
    bytes public  cd = '0x11';
    uint24[2][5] x = [[uint24(0x1), 1], [0xffffff, 2], [uint24(0xff), 3], [uint24(0xffff), 4], [0xffffff, 2]];

    function test(uint input) public payable {
        if (msg.value != 12 ether) 
            return;
        if (input < 1234 && input > 0x123)
            return;
        if (msg.sender != 0x5B38Da6a701c568545dCfcB03FcB875f56beddC4) 
            return;
        string memory test = "my_test_string";
        
    }
}