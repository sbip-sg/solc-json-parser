pragma solidity =0.8.4;
contract Test{
    struct TokenApprovalRef {
        address value;
    }
    
    mapping(uint256 => TokenApprovalRef) private _tokenApprovals;
    
    function accessAssemblyMemberlist(uint256 _id) public view
        returns (uint256 approvedAddressSlot, address approvedAddress) {
        TokenApprovalRef storage tokenApproval = _tokenApprovals[_id];
        assembly {
            approvedAddressSlot := tokenApproval.slot // <----- tokenApproval.slot is causing the error
            approvedAddress := sload(approvedAddressSlot)
        }
    }
}
