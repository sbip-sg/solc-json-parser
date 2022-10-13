pragma solidity ^0.7.0;
contract Attacker{
    fallback() external{
        revert();
    }
}