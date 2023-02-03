pragma solidity ^0.8.0;
contract Test {
     mapping (address => bool) test;
     modifier onlyOwner {
      require(true);
      _;
    }
    modifier onlyAdmin {
      require(true);
      _;
    }
    function test_func(address input)
         public
            onlyOwner{
        address(input).call("0x1234");
        test[input] = true;
    }
    function self_destruct()
        public
        onlyAdmin {
        selfdestruct(payable(msg.sender));
    }
}
