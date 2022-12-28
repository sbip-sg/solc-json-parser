from dataclasses import dataclass
import unittest
from solc_json_parser.flatten import FlattenSolidity
from typing import Dict, Any, Iterable, List

@dataclass
class ExpectedLineMapping:
    filename: str
    sourceLineNum: int
    sourceLine: str
    targetLineNum: int


class TestCase():
    def __init__(self, path: str, expected_line_mappings = Iterable[ExpectedLineMapping]):
        self.path = path
        self.expected_line_mappings = expected_line_mappings

class TestSourceByPc(unittest.TestCase):
    def test_flatten_line_mapping_with_no_imports(self):
        test_cases = [
            TestCase(
                './tests/test_contracts/flatten/A.sol',
                [ExpectedLineMapping('A.sol', 0, '// SPDX-License-Identifier: MIT', 0),
                 ExpectedLineMapping('A.sol', 0, '// SPDX-License-Identifier: MIT', 0),])
        ]
        for t in test_cases:
            f = FlattenSolidity(t.path)
            for e in t.expected_line_mappings:
                self.assertEqual(f.reverse_line_lookup(e.targetLineNum)[1], e.targetLineNum, f'Flatten line mapping error with source {t.path}: {e}')


    def test_flatten_line_mapping_with_single_imports(self):
        test_cases = []
        for t in test_cases:
            pass


    def test_flatten_line_mapping_with_multiple_imports(self):
        test_cases = []
        for t in test_cases:
            pass
