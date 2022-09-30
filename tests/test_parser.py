import unittest

import solc_json_parser as parser
from solc_ast_parser import SolidityAST
contracts_root = '../contracts'

class TestParser(unittest.TestCase):
    def test_get_correct_version(self):
        ast, versions = parser.compile_to_json(f'{contracts_root}/inheritance_contracts.sol')
        self.assertEqual(list, type(versions), 'Should return a list of versions')
        self.assertEqual(['>=0.7.2'], versions, 'Contract version incorrectly identified')

    def test_get_all_contracts(self):
        expected_contract_names = set(['A', 'B', 'C'])
        ast, version = parser.compile_to_json(f'{contracts_root}/inheritance_contracts.sol')
        expected_contract_names = None
        all_contract_names = set([c.get('name') for c in expected_contract_names])
        self.assertEqual(expected_contract_names, all_contract_names, 'Contracts should be identified correctly')

    def test_get_functions_by_contract(self):
        ast, versions = parser.compile_to_json(f'{contracts_root}/inheritance_contracts.sol')
        contract_name = 'C'
        fns = None

    # add tests
    def test_get_version(self):
        ast = SolidityAST(f'{contracts_root}/buy051.sol')
        self.assertEqual('0.5.1', ast.get_version(), 'Version should be 0.5.1')

        ast = SolidityAST(f'{contracts_root}/inheritance_contracts.sol')
        self.assertEqual('0.7.2', ast.get_version(), 'Version should be 0.7.2')
        
        

        



if __name__ == '__main__':
    unittest.main()

