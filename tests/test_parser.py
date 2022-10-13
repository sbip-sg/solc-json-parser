import unittest
from solc_json_parser.parser import SolidityAst
contracts_root = './contracts'

class TestParser(unittest.TestCase):
    FIELD_VISIBILITY_ALL = frozenset(
        ('default', 'internal', 'public', 'private'))
    FIELD_VISIBILITY_NON_PRIVATE = frozenset(('default', 'internal', 'public'))

    FUNC_VISIBILITY_ALL = frozenset(
        ('external', 'private', 'internal', 'public'))

    # add tests
    def test_get_version(self):
        ast = SolidityAst(f'{contracts_root}/buy051.sol')
        self.assertEqual('0.5.1', ast.exact_version, 'Version should be 0.5.1')

        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')
        self.assertEqual('0.7.2', ast.exact_version, 'Version should be 0.7.2')

    def test_all_contract_name(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')
        expected_contract_names = {'A', 'B', 'C'}
        all_contract_names = set(ast.all_contract_names())
        self.assertEqual(expected_contract_names, all_contract_names, 'Contracts should be identified correctly')
        
        
    def test_base_contract_names(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')
        expected_base_contract_names = {'A'}
        base_contract_names = set(ast.base_contract_names())
        self.assertEqual(expected_base_contract_names, base_contract_names, 'Base contracts should be identified correctly')
        
    def test_pruned_contract_names(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')
        expected_pruned_contract_names = {'B', 'C'}
        pruned_contract_names = set(ast.pruned_contract_names())
        self.assertEqual(expected_pruned_contract_names, pruned_contract_names, 'Pruned contracts should be identified correctly')


    def test_fields_name_only_in_contract(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')
        contract_a = ast.contract_by_name('A')
        fields_name_a = set(ast.fields_in_contract(contract_a, name_only=True))
        expected_fields_name_a = {'offering', 'threshold', 'level', 'balancesA', 'step', 'private_var'}
        self.assertEqual(expected_fields_name_a, fields_name_a, 'Fields_a should be identified correctly')

        contract_b = ast.contract_by_name('B')
        fields_name_b = set(ast.fields_in_contract(contract_b, name_only=True))
        expected_fields_name_b = {'owner', 'val', 'call'}
        self.assertEqual(expected_fields_name_b, fields_name_b, 'Fields_b should be identified correctly')

        contract_c = ast.contract_by_name('C')
        fields_name_c = set(ast.fields_in_contract(contract_c, name_only=True))
        expected_fields_name_c = {'owner', 'b', 'grade', 'mc'}
        self.assertEqual(expected_fields_name_c, fields_name_c, 'Fields_c without base should be identified correctly')

        fields_name_c = set(ast.fields_in_contract(contract_c, name_only=True, with_base_fields=True))
        expected_fields_name_c = {'owner', 'b', 'grade', 'mc', 'offering', 'level', 'threshold', 'balancesA', 'step'}
        self.assertEqual(expected_fields_name_c, fields_name_c, 'Fields_c with base should be identified correctly')

    def test_fields_in_contract_by_name(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')

        # fields_a all
        fields_name_a = set(ast.fields_in_contract_by_name('A', name_only=True, field_visibility=self.FIELD_VISIBILITY_ALL))
        expected_fields_name_a = {'offering', 'threshold', 'level', 'balancesA', 'step', 'private_var'}
        self.assertEqual(expected_fields_name_a, fields_name_a, 'Fields_a should be identified correctly')

        # fields_a non-private
        fields_name_a = set(ast.fields_in_contract_by_name('A', name_only=True, field_visibility=self.FIELD_VISIBILITY_NON_PRIVATE))
        expected_fields_name_a = {'offering', 'threshold', 'level', 'balancesA', 'step'}
        self.assertEqual(expected_fields_name_a, fields_name_a, 'Fields_a should be identified correctly')

        # fields_c
        fields_name_c = set(ast.fields_in_contract_by_name('C', name_only=True, with_base_fields=True))
        expected_fields_name_c = {'owner', 'b', 'grade', 'mc', 'offering', 'level', 'threshold', 'balancesA', 'step'}
        self.assertEqual(expected_fields_name_c, fields_name_c, 'Fields_c with base should be identified correctly')

        # fields_c without base fields
        fields_name_c = set(ast.fields_in_contract_by_name('C', name_only=True, with_base_fields=False))
        expected_fields_name_c = {'owner', 'b', 'grade', 'mc'}
        self.assertEqual(expected_fields_name_c, fields_name_c, 'Fields_c without base should be identified correctly')

    def test_functions_in_contract_by_name_with_name_only(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')

        functions_a = set(ast.functions_in_contract_by_name('A', name_only=True))
        expected_functions_a = {'absfunc', 'emptyfunc', 'receive'}
        self.assertEqual(expected_functions_a, functions_a, 'Functions_a should be identified correctly')

        functions_b = set(ast.functions_in_contract_by_name('B', name_only=True))
        expected_functions_b = {'constructor', 'touch'}
        self.assertEqual(expected_functions_b, functions_b, 'Functions_b should be identified correctly')

        functions_c = set(ast.functions_in_contract_by_name('C', name_only=True, check_base_contract=False))
        expected_functions_c = {'constructor', 'absfunc', 'cmasking', 'sweep', 'guess', 'cread', 'cwrite'}
        self.assertEqual(expected_functions_c, functions_c, 'Functions_c should be identified correctly')

        functions_c = set(ast.functions_in_contract_by_name('C', name_only=True, check_base_contract=True))
        expected_functions_c = {'constructor', 'absfunc', 'cmasking', 'sweep', 'guess', 'cread', 'cwrite',
                                'emptyfunc', 'receive'}
        self.assertEqual(expected_functions_c, functions_c, 'Functions_c should be identified correctly')


    def test_optional_version_input(self):
        ast_with_version = SolidityAst(f'{contracts_root}/inheritance_contracts.sol', version='0.7.4')
        ast_without_version = SolidityAst(f'{contracts_root}/inheritance_contracts.sol', version=None)
        self.assertEqual('0.7.4', ast_with_version.exact_version, 'AST should be the same with and without version input')
        self.assertEqual('0.7.2', ast_without_version.exact_version, 'AST should be the same with and without version input')

    def test_get_plain_version_from_source(self):
        path = f'{contracts_root}/inheritance_contracts.sol'
        t_cases = [('whole.sol', '^0.8.0'), ('buy051.sol', '0.5.1')]

        for (c, ver) in t_cases:
            path = f'{contracts_root}/{c}'
            ast = SolidityAst(path)
            self.assertEqual(ver, ast.raw_version)

    def test_parser(self):
        import glob
        inputs = glob.glob('contracts/*.sol')
        for c in inputs :
            try:
                self.assertIsNotNone(SolidityAst(c), f'Test contract failed: {c}')
            except Exception as e:
                print(f'Parsing {c} failed with {e}')
            

if __name__ == '__main__':
    unittest.main()

