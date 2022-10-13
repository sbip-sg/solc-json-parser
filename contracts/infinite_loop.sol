pragma solidity ^0.7.0;
contract Test {
    int a;
    function test1 (int input) public returns(int){
        while(true){
            a = a+1;
            address(0xfD36E2c2a6789Db23113685031d7F16329158384).call("");
        }
    }
 }

contract Test2 {
    int a;
    function test1 (int input) public returns(int){
        while(true){
            a = a+1;
        }
    }
 }