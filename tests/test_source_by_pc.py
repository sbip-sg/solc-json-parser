import unittest
from solc_json_parser.parser import SolidityAst, get_in

class TestSourceByPc(unittest.TestCase):
    def test_source_by_pc_single_source(self):
        test_cases = [
            ('./tests/test_contracts/IntegerOverflow.sol',
             'IntegerOverflow',
             False,
             ((333, 9),
              (383, 11),
              (85, 19),
              (321, 16),
              (338, 9),
              (377, 10),)),
            ('./tests/test_contracts/ms/MultiSourceLib.sol',
             'MultiSourceUtils',
             False,
             ((123, 15),))
        ]
        for (path, contract, use_deploy_code, lns) in test_cases:
            ast = SolidityAst(path)
            for (pc, linenum) in lns:
                frag = ast.source_by_pc(contract, pc, use_deploy_code)
                ln = get_in(frag, 'linenums', 0)
                self.assertEqual(linenum, ln, f'Fail with contract {contract} in {path}')

    def test_source_by_pc_multiple_sources(self):
        test_cases = [
            ('./tests/test_contracts/ms/MultiSource.sol',
             'MultiSourceUtils',
             False,
             (
                 (123, 15),
              )),
            ('./tests/test_contracts/ms/MultiSource.sol',
             'MultiSource',
             False,
             (
                 (132, 17),
              )),
        ]
        for (path, contract, use_deploy_code, lns) in test_cases:
            ast = SolidityAst(path)
            for (pc, linenum) in lns:
                frag = ast.source_by_pc(contract, pc, use_deploy_code)
                ln = get_in(frag, 'linenums', 0)
                self.assertEqual(linenum, ln, f'Fail with contract {contract} in {path} {frag}')
