// SPDX-License-Identifier: Academic Free License v1.1
// A sample contract for testing extraction of fields by AST

pragma solidity >=0.7.2;

abstract contract A {
    event Received(address, uint256);
    // publicly accessible
    uint256 public offering = 256;
    uint256 public constant threshold = 28889;

    // accessible to itself and by the inherited contract
    uint256 internal level = 23;
    // same as internal
    uint256 step = 23;
    mapping(address => uint256) balancesA;

    function absfunc(uint256) public virtual returns (uint256);

    function emptyfunc(uint256) public {}

    // this contract accepts ether payments
    receive() external payable {
        emit Received(msg.sender, msg.value);
    }
}

contract B {
    address owner;
    uint256 val = 0;
    uint256 call = 3;

    constructor() {
        owner = msg.sender;
    }

    function touch() external returns (uint256) {
        val = val + 1;
        return val;
    }
}

contract C is A {
    address payable owner;
    B b;

    uint256 grade = 0;
    uint256 mc = 9;

    constructor(address bAddress) {
        owner = payable(msg.sender);
        b = B(bAddress);
    }

    function absfunc(uint256) public override returns (uint256){
        return grade;
    }
    
    function cmasking(uint256 maskval) external returns (uint256) {
        uint256 v = maskval;
        // 1. A.level should not be considered as read
        //    Note: Compiler shows warning for such use case.
        uint256 unused = level;

        {
            level *= 2;

            // 2. A.threshold is masked here
            uint256 threshold = level;
            uint256 insider = threshold / 2 + offering++;

            if (offering++ % insider == 0) {
                uint256 mc = 8;
                // 4. First return statement
                return offering * mc;
            }

            //mc++;
        }

        // 3. A.threshold is in scope again here
        // 5. Second return statement
        return offering + (v % threshold) + grade * 10;
    }

    function sweep() external {
        require(msg.sender == owner, "Only owner can sweep ethers in contract");
        uint256 balance = address(this).balance;
        require(balance > 0, "Nothing to sweep");

        uint256 ownerBalance = owner.balance;
        bool success;
        if (ownerBalance > 1000 * balance) {
            (success,)  = owner.call{value: balance / 10}("");
        } else {
            (success,)  = owner.call{value: balance}("");
        }
        require(success, "Transfer failed");
    }

    function guess(uint256 n) external {
        uint256 g = uint256(
            keccak256(abi.encodePacked(block.timestamp, msg.sender, n))
        );
        address to = msg.sender;
        if (g < threshold) {
            (bool success, ) = to.call{value: 9765}("");
            require(success, "Send faild");

            owner.transfer(9764);
            success = owner.send(9763);
            require(success, "Send faild");
        }
        b.touch();
    }

    function cread() public view returns (uint256) {
        if (address(this).balance > grade * 10) {
            return offering;
        } else {
            return 0;
        }
    }

    function cwrite(uint256 val) external payable returns (uint256) {
        uint256 share = msg.value / 10;
        payable(address(0x6d79E25291F7825cDf9594a805899EE50EA23809)).transfer(
            100
        );

        require(share > 2300, "Requies minimum send value");
        offering = offering + val;
        return offering;
    }
}
