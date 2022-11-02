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
              (377, 10),))
        ]
        for (path, contract, use_deploy_code, lns) in test_cases:
            ast = SolidityAst(path)
            for (pc, linenum) in lns:
                frag = ast.source_by_pc(contract, pc, use_deploy_code)
                ln = get_in(frag, 'linenums', 0)
                self.assertEqual(linenum, ln, f'Fail with contract {contract} in {path}')

if __name__ == '__main__':
    unittest.main()
