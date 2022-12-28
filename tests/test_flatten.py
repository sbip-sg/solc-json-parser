from dataclasses import dataclass
import unittest
from solc_json_parser.flatten import FlattenLine, FlattenSolidity

class TestCase():
    def __init__(self, path: str, expected_line_mappings = [FlattenLine]):
        self.path = path
        self.expected_line_mappings = expected_line_mappings


class TestSourceByPc(unittest.TestCase):
    def run_tests(self, *test_cases):
        for t in test_cases:
            f = FlattenSolidity(t.path)
            for e in t.expected_line_mappings:
                fline = f.reverse_line_lookup(e.targetLineNum)
                hint = '{actual} != {expected}'
                self.assertEqual(fline.sourceLineNum, e.sourceLineNum, f'{hint} @ {t.path}: {e}')
                self.assertEqual(fline.sourceLine.strip(), e.sourceLine.strip(), f'{hint} @ {t.path}: {e}')
                self.assertEqual(fline.filename, e.filename, f'{hint} @ {t.path}: {e}')

    def test_flatten_line_mapping_with_no_imports(self):
        self.run_tests(TestCase(
            './tests/test_contracts/flatten/A.sol',
            [
                FlattenLine('path_ignored', 'A.sol', 3, 'contract A{', 3, 'contract A{'),
            ]))


    def test_flatten_line_mapping_with_single_imports(self):
        self.run_tests(TestCase(
            './tests/test_contracts/flatten/B.sol',
            [
                FlattenLine('path_ignored', 'A.sol', 3, 'contract A{', 7, 'contract A{'),
                FlattenLine('path_ignored', 'B.sol', 5, 'contract B{', 11, 'contract B{'),
            ]))



    def test_flatten_line_mapping_with_multiple_imports(self):
        self.run_tests(TestCase(
            './tests/test_contracts/flatten/C.sol',
            [
                FlattenLine('path_ignored', 'A.sol', 3, 'contract A{', 7, 'contract A{'),
                FlattenLine('path_ignored', 'B.sol', 5, 'contract B{', 16, 'contract B{'),
                FlattenLine('path_ignored', 'C.sol', 6, 'contract C{', 20, 'contract C{'),
            ]))

    def test_flatten_line_mapping_with_selective_imports(self):
        self.run_tests(TestCase(
            './tests/test_contracts/flatten/D.sol',
            [
                FlattenLine('path_ignored', 'A.sol', 3, 'contract A{', 7, 'contract A{'),
                FlattenLine('path_ignored', 'B.sol', 5, 'contract B{', 24, 'contract B{'),
                FlattenLine('path_ignored', 'C.sol', 6, 'contract C{', 28, 'contract C{'),
                FlattenLine('path_ignored', 'D.sol', 9, 'contract D{', 32, 'contract D{'),
            ]))
