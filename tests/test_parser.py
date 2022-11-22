import unittest
from solc_json_parser.parser import SolidityAst, SolidityAstError
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
        all_contract_names = set(ast.all_contract_names)
        self.assertEqual(expected_contract_names, all_contract_names, 'Contracts should be identified correctly')
        
        
    def test_base_contract_names(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')
        expected_base_contract_names = {'A'}
        base_contract_names = set(ast.base_contract_names)
        self.assertEqual(expected_base_contract_names, base_contract_names, 'Base contracts should be identified correctly')
        
    def test_pruned_contract_names(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')
        expected_pruned_contract_names = {'B', 'C'}
        pruned_contract_names = set(ast.pruned_contract_names)
        self.assertEqual(expected_pruned_contract_names, pruned_contract_names, 'Pruned contracts should be identified correctly')

        ast = SolidityAst(f'{contracts_root}/whole.sol')
        expected_pruned_contract_names = {'BeeArmyRankNFT'}
        pruned_contract_names = set(ast.pruned_contract_names)
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
            
    def test_line_number_range_v7(self):
        ast = SolidityAst(f'{contracts_root}/inheritance_contracts.sol')
        
        # test contract A
        contract_a = ast.contract_by_name('A')
        expected_range_a = (6, 27)
        self.assertEqual(expected_range_a, contract_a.line_num, 'Contract A should have correct line number range')
        
        # test contract B
        contract_b = ast.contract_by_name('B')
        expected_range_b = (29, 42)
        self.assertEqual(expected_range_b, contract_b.line_num, 'Contract B should have correct line number range')
        
        # B.constructor function
        expected_function_range = (34, 36)
        function_range = ast.function_by_name('B', 'constructor').line_num
        self.assertEqual(expected_function_range, function_range)
        
        # B.touch function
        expected_function_range = (38, 41)
        function_range = ast.function_by_name('B', 'touch').line_num
        self.assertEqual(expected_function_range, function_range)
        
        # B.owner; B.val; B.call; Fields
        fields = ast.fields_in_contract_by_name('B')
        
        expected_field_range = (30, 30)
        field_range = fields[0].line_num
        self.assertEqual(expected_field_range, field_range)
        
        expected_field_range = (31, 31)
        field_range = fields[1].line_num
        self.assertEqual(expected_field_range, field_range)
        
        expected_field_range = (32, 32)
        field_range = fields[2].line_num
        self.assertEqual(expected_field_range, field_range)
        
        
        # test contract C
        contract_c = ast.contract_by_name('C')
        expected_range_c = (44, 136)
        self.assertEqual(expected_range_c, contract_c.line_num, 'Contract C should have correct line number range')
        
        # C.cmasking function
        expected_function_range = (60, 85)
        function_range = ast.function_by_name('C', 'cmasking').line_num
        self.assertEqual(expected_function_range, function_range)
        
        # C.sweep function
        expected_function_range = (87, 100)
        function_range = ast.function_by_name('C', 'sweep').line_num
        self.assertEqual(expected_function_range, function_range)
        
    def test_line_number_range_v8(self):
        ast = SolidityAst(f'{contracts_root}/whole.sol')
        contract = ast.contract_by_name('BEPContext')
        expected_range = (20, 33)
        self.assertEqual(expected_range, contract.line_num, 'Contract BEPContext should have correct line number range')

        contract = ast.contract_by_name('BEPOwnable')
        expected_range = (48, 112)
        self.assertEqual(expected_range, contract.line_num, 'Contract BEPOwnable should have correct line number range')

        contract = ast.contract_by_name('Address')
        expected_range = (241, 454)
        self.assertEqual(expected_range, contract.line_num, 'Contract Address should have correct line number range')

        expected_function_range = (178, 198)
        function_range = ast.function_by_name('Strings', 'toString').line_num
        self.assertEqual(expected_function_range, function_range)

        expected_function_range = (346, 352)
        function_range = ast.function_by_name('Address', 'functionCallWithValue').line_num
        self.assertEqual(expected_function_range, function_range)

        expected_function_range = (1146, 1167)
        function_range = ast.function_by_name('ERC721', '_checkOnERC721Received').line_num
        self.assertEqual(expected_function_range, function_range)

        fields = ast.fields_in_contract_by_name('ERC721Enumerable')
        expected_field_range = (1225, 1225)
        field_range = fields[0].line_num
        self.assertEqual(expected_field_range, field_range)

        expected_field_range = (1228, 1228)
        field_range = fields[1].line_num
        self.assertEqual(expected_field_range, field_range)

        expected_field_range = (1234, 1234)
        field_range = fields[3].line_num
        self.assertEqual(expected_field_range, field_range)

    def test_line_number_range_v4(self):
        ast = SolidityAst(f'{contracts_root}/reentrancy_dao.sol')
        contract = ast.contract_by_name('ReentrancyDAO')
        expected_range = (3, 21)
        self.assertEqual(expected_range, contract.line_num, 'ReentrancyDAO BEPContext should have correct line number range')

        expected_function_range = (7, 15)
        function_range = ast.function_by_name('ReentrancyDAO', 'withdrawAll').line_num
        self.assertEqual(expected_function_range, function_range)

        expected_function_range = (17, 20)
        function_range = ast.function_by_name('ReentrancyDAO', 'deposit').line_num
        self.assertEqual(expected_function_range, function_range)

        fields = ast.fields_in_contract_by_name('ReentrancyDAO')
        expected_field_range = (4, 4)
        field_range = fields[0].line_num
        self.assertEqual(expected_field_range, field_range)

        expected_field_range = (5, 5)
        field_range = fields[1].line_num
        self.assertEqual(expected_field_range, field_range)

    def test_multi_src_file_v8(self):
        ast = SolidityAst(f'{contracts_root}/dev/dev.sol')
        # todo more test
        
    def test_all_library(self):
        ast = SolidityAst(f'{contracts_root}/whole.sol')
        lib_name = ast.all_libraries_names
        expected_lib_name = ["Strings", "Address"]
        self.assertEqual(expected_lib_name, lib_name, 'Should have correct library names')

    def test_fall_back(self):
        # for v6-v8
        ast = SolidityAst(f'{contracts_root}/dev/fallback.sol')
        funcs = ast.functions_in_contract_by_name('Fallback')

        func_kind = [func.kind for func in funcs]
        expected_func_kind = ['receive', 'function', 'function', 'fallback']
        self.assertEqual(expected_func_kind, func_kind, 'Should have correct function kind')

        state_mutability = [func.state_mutability for func in funcs]
        expected_state_mutability = ['payable', 'payable', 'payable', 'nonpayable']
        self.assertEqual(expected_state_mutability, state_mutability, 'Should have correct state_mutability')

        # for v4 and v5
        ast = SolidityAst(f'{contracts_root}/dev/fallback04.sol')
        funcs = ast.functions_in_contract_by_name('Fallback')
        func_kind = [func.kind for func in funcs]
        expected_func_kind = ['fallback', 'function', 'function']
        self.assertEqual(expected_func_kind, func_kind, 'Should have correct function kind')

        func_name = [func.name for func in funcs]
        expected_func_name = ['fallback', 'receive', 'fallback']
        self.assertEqual(expected_func_name, func_name, 'Should have correct function name')


    def test_program_counter(self):
        contracts_root = "./contracts"
        ast = SolidityAst(f'{contracts_root}/dev/1_BaseStorage.sol')
        x = ast.source_by_pc(contract_name='Storage', pc=234, deploy=False)
        # print(x)

    def test_add_automatic_retrying(self):
        # this will work
        ast = SolidityAst(f'{contracts_root}/dev/buggy_10.sol', retry_num=10)

        # this will fail
        try:
            ast = SolidityAst(f'{contracts_root}/dev/buggy_10.sol', retry_num=0)
        except SolidityAstError:
            print("SolidityAstError is expected")

    def test_unicode_characters(self):
        contracts_root = "../contracts"
        ast = SolidityAst(f'{contracts_root}/dev/buggy20.sol', version='0.5.11')
        functions = ast.abstract_function_in_contract_by_name('RampInstantEscrowsPoolInterface')
        self.assertTrue(functions[0].raw.startswith("function"))
        print(functions[0])

