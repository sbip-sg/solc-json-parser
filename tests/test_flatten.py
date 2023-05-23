from dataclasses import dataclass
import unittest
from solc_json_parser.flatten import FlattenLine, FlattenSolidity

class ExpectedMapping():
    def __init__(self, path: str, expected_line_mappings = [FlattenLine]):
        self.path = path
        self.expected_line_mappings = expected_line_mappings


class TestSourceByPc(unittest.TestCase):
    def run_tests(self, *test_cases):
        for t in test_cases:
            f = FlattenSolidity(t.path)
            for e in t.expected_line_mappings:
                fline = f.reverse_line_lookup(e.targetLineNum)
                hint = f'Actual: {fline} != Expected: f{e}'
                self.assertEqual(fline.sourceLineNum, e.sourceLineNum, f'{hint} @ {t.path}: {e}')
                self.assertEqual(fline.sourceLine.strip(), e.sourceLine.strip(), f'{hint} @ {t.path}: {e}')
                self.assertEqual(fline.filename, e.filename, f'{hint} @ {t.path}: {e}')

    def test_flatten_line_mapping_with_no_imports(self):
        self.run_tests(ExpectedMapping(
            './tests/test_contracts/flatten/A.sol',
            [
                FlattenLine('path_ignored', 'A.sol', 3, 'contract A{', 3, 'contract A{'),
            ]))


    def test_flatten_line_mapping_with_single_imports(self):
        self.run_tests(ExpectedMapping(
            './tests/test_contracts/flatten/B.sol',
            [
                FlattenLine('path_ignored', 'A.sol', 3, 'contract A{', 7, 'contract A{'),
                FlattenLine('path_ignored', 'B.sol', 5, 'contract B{', 11, 'contract B{'),
            ]))



    def test_flatten_line_mapping_with_multiple_imports(self):
        self.run_tests(ExpectedMapping(
            './tests/test_contracts/flatten/C.sol',
            [
                FlattenLine('path_ignored', 'A.sol', 3, 'contract A{', 7, 'contract A{'),
                FlattenLine('path_ignored', 'B.sol', 5, 'contract B{', 16, 'contract B{'),
                FlattenLine('path_ignored', 'C.sol', 6, 'contract C{', 20, 'contract C{'),
            ]))

    def test_flatten_line_mapping_with_selective_imports(self):
        self.run_tests(ExpectedMapping(
            './tests/test_contracts/flatten/D.sol',
            [
                FlattenLine('path_ignored', 'A.sol', 3, 'contract A{', 7, 'contract A{'),
                FlattenLine('path_ignored', 'B.sol', 5, 'contract B{', 24, 'contract B{'),
                FlattenLine('path_ignored', 'C.sol', 6, 'contract C{', 28, 'contract C{'),
                FlattenLine('path_ignored', 'D.sol', 9, 'contract D{', 32, 'contract D{'),
            ]))


    def test_flatten_line_mapping_with_complex_01_contract(self):
        self.run_tests(ExpectedMapping(
            './tests/test_contracts/flatten/01/01_13_INSURToken.sol',
            [
                FlattenLine('path_ignored', '01_13_INSURToken.sol', 56, 'function addSender(address _from) external onlyAdmin {', 1723, 'function addSender(address _from) external onlyAdmin {'),
                FlattenLine('path_ignored', '01_13_INSURToken.sol', 140, 'function delegate(address _delegatee) external {', 1807, 'function delegate(address _delegatee) external {'),
                FlattenLine('path_ignored', '04_13_AccessControlUpgradeable.sol', 142, 'function grantRole(bytes32 role, address account) public virtual {', 718, 'function grantRole(bytes32 role, address account) public virtual {'),
            ]))

    def test_flatten_line_mapping_with_complex_02_contract(self):
        self.run_tests(ExpectedMapping(
            './tests/test_contracts/flatten/02/01_20_RubicProxy.sol',
            [
                FlattenLine('path_ignored', '01_20_RubicProxy.sol', 119, 'function sweepTokens(address _token, uint256 _amount) external onlyAdmin {', 2429, 'function sweepTokens(address _token, uint256 _amount) external onlyAdmin {'),
                FlattenLine('path_ignored', '04_20_BridgeBase.sol', 342, 'function setMinTokenAmount(address _token, uint256 _minTokenAmount) external onlyManagerOrAdmin {', 2169, 'function setMinTokenAmount(address _token, uint256 _minTokenAmount) external onlyManagerOrAdmin {'),
                FlattenLine('path_ignored', '04_20_BridgeBase.sol', 355, 'function setMaxTokenAmount(address _token, uint256 _maxTokenAmount) external onlyManagerOrAdmin {', 2182, 'function setMaxTokenAmount(address _token, uint256 _maxTokenAmount) external onlyManagerOrAdmin {'),

            ]))
