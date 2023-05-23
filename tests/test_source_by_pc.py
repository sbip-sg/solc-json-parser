import unittest
from solc_json_parser.combined_json_parser import CombinedJsonParser
from solc_json_parser.ast_shared import get_in
from typing import Dict, Any, List


class ExpectedResult():
    def __init__(self, source: str, contract: str, use_deploy_code: bool, expected_pc_start_lines = List, solc_options: Dict={}):
        self.source = source
        self.contract = contract
        self.use_deploy_code = use_deploy_code
        self.solc_options = solc_options
        self.expected_pc_start_lines = expected_pc_start_lines

class TestSourceByPc(unittest.TestCase):
    def test_source_by_pc_single_source(self):
        test_cases = [
            ExpectedResult('./tests/test_contracts/IntegerOverflow.sol',
                     'IntegerOverflow',
                     False,
                     [(333, 9),
                      (383, 11),
                      (85, 19),
                      (321, 16),
                      (338, 9),
                      (377, 10),]),
            ExpectedResult('./tests/test_contracts/ms/MultiSourceLib.sol',
                     'MultiSourceUtils',
                     False,
                     [(123, 15),]),
            ExpectedResult('./tests/test_contracts/test_with_exp_abi.sol',
                     'Test',
                     False,
                     [(278, 15),
                      (293, 16)],
                     {'optimize': True, 'optimize_runs': 200}),
            ExpectedResult('./tests/test_contracts/Test.sol',
                     'Test',
                     False,
                     [(200, 14),
                      (218, 15)],
                     {'optimize': True, 'optimize_runs': 200})]
        for t in test_cases:
            ast = CombinedJsonParser(t.source, solc_options=t.solc_options)
            for (pc, linenum) in t.expected_pc_start_lines:
                frag = ast.source_by_pc(t.contract, pc, t.use_deploy_code)
                ln = get_in(frag, 'linenums', 0)
                self.assertEqual(linenum, ln, f'Fail with contract {t.contract} in {t.source} with options {t.solc_options}, got fragment: {frag}')

    def test_source_by_pc_multiple_sources(self):
        test_cases = [
            ExpectedResult('./tests/test_contracts/ms/MultiSource.sol',
                     'MultiSourceUtils',
                     False,
                     [(123, 15),]),
            ExpectedResult('./tests/test_contracts/ms/MultiSource.sol',
                     'MultiSource',
                     False,
                     [(132, 17),]),
        ]
        for t in test_cases:
            ast = CombinedJsonParser(t.source)
            for (pc, linenum) in t.expected_pc_start_lines:
                frag = ast.source_by_pc(t.contract, pc, t.use_deploy_code)
                ln = get_in(frag, 'linenums', 0)
                self.assertEqual(linenum, ln, f'Fail with contract {t.contract} in {t.source} with options {t.solc_options}, got fragment: {frag}')
