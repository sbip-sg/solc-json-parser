import unittest
from solc_json_parser.combined_json_parser import CombinedJsonParser, SolidityAstError
contracts_root = './contracts'


class TestParser(unittest.TestCase):
    FIELD_VISIBILITY_ALL = frozenset(
        ('default', 'internal', 'public', 'private'))
    FIELD_VISIBILITY_NON_PRIVATE = frozenset(('default', 'internal', 'public'))

    FUNC_VISIBILITY_ALL = frozenset(
        ('external', 'private', 'internal', 'public'))

    # add tests
    def test_get_version(self):
        ast = CombinedJsonParser(f'{contracts_root}/buy051.sol')
        self.assertEqual('0.5.1', ast.exact_version, 'Version should be 0.5.1')

        ast = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol')
        self.assertIn('0.7.2', ast.allowed_solc_versions, '0.7.2 should be in solc candidate list')

    def test_all_contract_name(self):
        ast = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol')
        expected_contract_names = {'A', 'B', 'C'}
        all_contract_names = set(ast.all_contract_names)
        self.assertEqual(expected_contract_names, all_contract_names, 'Contracts should be identified correctly')

    def test_base_contract_names(self):
        ast = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol')
        expected_base_contract_names = {'A'}
        base_contract_names = set(ast.base_contract_names)
        self.assertEqual(expected_base_contract_names, base_contract_names, 'Base contracts should be identified correctly')

    def test_pruned_contract_names(self):
        ast = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol')
        expected_pruned_contract_names = {'B', 'C'}
        pruned_contract_names = set(ast.pruned_contract_names)
        self.assertEqual(expected_pruned_contract_names, pruned_contract_names, 'Pruned contracts should be identified correctly')

        ast = CombinedJsonParser(f'{contracts_root}/whole.sol')
        expected_pruned_contract_names = {'BeeArmyRankNFT'}
        pruned_contract_names = set(ast.pruned_contract_names)
        self.assertEqual(expected_pruned_contract_names, pruned_contract_names, 'Pruned contracts should be identified correctly')

    def test_fields_name_only_in_contract(self):
        ast = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol')
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
        ast = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol')

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
        ast = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol')

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
        ast_with_version = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol', version='0.7.4')
        ast_without_version = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol', version=None)
        self.assertEqual('0.7.4', ast_with_version.exact_version, 'AST should be the same with and without version input')
        self.assertIn('0.7.2', ast_without_version.allowed_solc_versions, 'AST should be the same with and without version input')

    def test_get_plain_version_from_source(self):
        path = f'{contracts_root}/inheritance_contracts.sol'
        t_cases = [('whole.sol', '^0.8.0'), ('buy051.sol', '0.5.1')]

        for (c, ver) in t_cases:
            path = f'{contracts_root}/{c}'
            ast = CombinedJsonParser(path)
            self.assertEqual(ver, ast.raw_version)

    def test_parser(self):
        import glob
        inputs = glob.glob('contracts/*.sol')
        for c in inputs:
            try:
                self.assertIsNotNone(CombinedJsonParser(c), f'Test contract failed: {c}')
            except Exception as e:
                print(f'Parsing {c} failed with {e}')

    def test_line_number_range_v7(self):
        ast = CombinedJsonParser(f'{contracts_root}/inheritance_contracts.sol')

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
        ast = CombinedJsonParser(f'{contracts_root}/whole.sol')
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
        ast = CombinedJsonParser(f'{contracts_root}/reentrancy_dao.sol')
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

    def test_function_by_name_utf8(self):
        ast = CombinedJsonParser(f'./tests/test_contracts/rubic.sol')
        f = ast.function_by_name('BridgeBase', 'setMaxTokenAmount')
        self.assertEqual((2158, 2164), f.line_num)

        f = ast.function_by_name('RubicProxy', 'setMaxTokenAmount')
        self.assertEqual((2158, 2164), f.line_num)

    def test_multi_src_file_v8(self):
        ast = CombinedJsonParser(f'{contracts_root}/dev/dev.sol')
        # todo more test

    def test_all_library(self):
        ast = CombinedJsonParser(f'{contracts_root}/whole.sol')
        lib_name = ast.all_libraries_names
        expected_lib_name = ["Strings", "Address"]
        self.assertEqual(expected_lib_name, lib_name, 'Should have correct library names')

    def test_fall_back(self):
        # for v6-v8
        ast = CombinedJsonParser(f'{contracts_root}/dev/fallback.sol')
        funcs = ast.functions_in_contract_by_name('Fallback')

        func_kind = [func.kind for func in funcs]
        expected_func_kind = ['receive', 'function', 'function', 'fallback']
        self.assertEqual(expected_func_kind, func_kind, 'Should have correct function kind')

        state_mutability = [func.state_mutability for func in funcs]
        expected_state_mutability = ['payable', 'payable', 'payable', 'nonpayable']
        self.assertEqual(expected_state_mutability, state_mutability, 'Should have correct state_mutability')

        # for v4 and v5
        ast = CombinedJsonParser(f'{contracts_root}/dev/fallback04.sol')
        funcs = ast.functions_in_contract_by_name('Fallback')
        func_kind = [func.kind for func in funcs]
        expected_func_kind = ['fallback', 'function', 'function']
        self.assertEqual(expected_func_kind, func_kind, 'Should have correct function kind')

        func_name = [func.name for func in funcs]
        expected_func_name = ['fallback', 'receive', 'fallback']
        self.assertEqual(expected_func_name, func_name, 'Should have correct function name')

    def test_program_counter(self):
        ast = CombinedJsonParser(f'{contracts_root}/dev/1_BaseStorage_pc.sol', version='0.6.0', solc_options={'allow_paths': ""})
        expected_data = [
            (261, (7, 9),   (102, 166)),
            (262, (8, 8),   (156, 159)),
            (283, (19, 19), (479, 493)),
        ]
        for pc, expected_linenums, expected_range in expected_data:
            data = ast.source_by_pc(contract_name='Storage', pc=pc, deploy=False)
            self.assertEqual(expected_linenums, data['linenums'], 'Should have correct line number')
            self.assertEqual(expected_range, (data['begin'], data['end']), 'Should have correct range')

        # test with optimize=True
        ast = CombinedJsonParser(f'{contracts_root}/dev/test_pc.sol', solc_options={
            'optimize': True,
        })
        expected_data = [
            (278,  (15, 15), (465, 476)),
            (293,  (16, 16), (500, 511)),
            (99,   (14, 17), (366, 527)),
        ]
        for pc, expected_linenums, expected_range in expected_data:
            data = ast.source_by_pc(contract_name='Test', pc=pc, deploy=False)
            self.assertEqual(expected_linenums, data['linenums'], 'Should have correct range')
            self.assertEqual(expected_range, (data['begin'], data['end']), 'Should have correct range')


    def test_unicode_characters(self):
        ast = CombinedJsonParser(f'{contracts_root}/dev/buggy20.sol', version='0.5.11')
        functions = ast.abstract_function_in_contract_by_name('RampInstantEscrowsPoolInterface')
        self.assertTrue(functions[0].raw.startswith("function"))

    def test_add_automatic_retrying(self):
        # this will work
        ast = CombinedJsonParser(f'{contracts_root}/dev/buggy_10.sol', retry_num=10)

        # this will fail
        try:
            ast = CombinedJsonParser(f'{contracts_root}/dev/buggy_10.sol', retry_num=0)
        except SolidityAstError:
            print("SolidityAstError is expected")

    def test_event(self):
        def sub_test(_ast):
            events = _ast.events_in_contract_by_name('IPoolEvents')
            self.assertEqual(17, len(events))
            # first two and last two
            expected_name = ['Purchase', 'Sell', 'BeforeTokenTransfer', 'implicitType']
            actual_name = [event.name for event in events[:2] + events[-2:]]
            self.assertEqual(set(expected_name), set(actual_name))

            expected_signature = [
                'Purchase(address, uint256, uint256, uint256, uint256, int128)',
                'Sell(address, uint256, uint256, uint256, uint256, int128)',
                'BeforeTokenTransfer()',
                'implicitType(uint256)'
            ]
            actual_signature = [event.signature for event in events[:2] + events[-2:]]
            self.assertEqual(set(expected_signature), set(actual_signature))

            expected_line_num = [(6, 13), (15, 22), (88, 88), (90, 90)]
            actual_line_num = [event.line_num for event in events[:2] + events[-2:]]
            self.assertEqual(set(expected_line_num), set(actual_line_num))

            contract_data = ast.contract_by_name('IPoolEvents')
            self.assertEqual((5, 91), contract_data.line_num)

            event = ast.event_by_name('IPoolEvents', 'Purchase')
            self.assertEqual((6, 13), event.line_num)
            self.assertEqual('Purchase(address, uint256, uint256, uint256, uint256, int128)', event.signature)
            self.assertEqual('Purchase', event.name)

            events  = ast.events_in_contract_by_name('IPoolEvents')
            events2 = ast.events_in_contract(contract_data)
            self.assertEqual(17, len(events2))
            self.assertEqual(events, events2)

        for v in ['0.4.23', '0.5.0', '0.6.0', '0.7.0', '0.8.7', '0.8.17']:
            ast = CombinedJsonParser(f'{contracts_root}/dev/20_39_IPoolEvents_45678.sol', version=v)
            sub_test(ast)

    def test_function_parsing(self):
        ast = CombinedJsonParser(f'tests/test_contracts/FunctionSignature.sol')
        fn = ast.function_by_name('Test', 'test_func')
        self.assertEqual('test_func(address)', fn.signature)
        self.assertEqual({'onlyOwner'}, set(fn.modifiers))

    def test_multi_source_line_num_range(self):
        def sub_test(ast):
            functions = ast.functions_in_contract_by_name('Storage')
            self.assertEqual(9, len(functions))

            function_name = ['add_store', 'store', 'store_sec', 'get_balance']
            line_num = [(18, 20), (7, 9), (6, 8), (17, 19)]
            for i, name in enumerate(function_name):
                func = ast.function_by_name('Storage', name)
                self.assertEqual(line_num[i], func.line_num)

            func1 = ast.function_by_name('Storage', 'store_sec')
            func2 = ast.function_by_name('SecondStorage', 'store_sec')
            self.assertEqual(func1.raw, func2.raw)

        for v in ['0.6.0', '0.7.0', '0.8.7']:
            ast = CombinedJsonParser(f'{contracts_root}/dev/1_BaseStorage.sol', version=v,
                              solc_options={'allow_paths': f''})
            sub_test(ast)

        for v in ['0.8.8', '0.8.12', '0.8.15', '0.8.17']:
            ast = CombinedJsonParser(f'{contracts_root}/dev/1_BaseStorage.sol', version=v,
                              solc_options={'allow_paths': f'', 'base_path': f'{contracts_root}'})
            sub_test(ast)

    def test_mapping_yul(self):
        ast = CombinedJsonParser(f'{contracts_root}/dev/rubic.sol', version='0.8.10')
        expected_data = [
            (14004, (185, 185), (5927, 5980)),
            (13948, (173, 176), (5523, 5662)),
            (13959, (175, 175), (5623, 5656)),
        ]
        for pc, expected_linenums, expected_range in expected_data:
            data = ast.source_by_pc(contract_name='RubicProxy', pc=pc, deploy=False)
            self.assertEqual(data.get('source_path'), '#utility.yul', 'Should have correct yul path')
            self.assertEqual(expected_linenums, data['linenums'], 'Should have correct range')
            self.assertEqual(expected_range, (data['begin'], data['end']), 'Should have correct range')

    def test_get_all_literals(self):
        ast7 = CombinedJsonParser(f'{contracts_root}/dev/test_literals.sol', version='0.7.0')
        ast8 = CombinedJsonParser(f'{contracts_root}/dev/test_literals.sol', version='0.8.17')

        for ast in [ast7, ast8]:
            literals = ast.get_literals("Test", only_value=True)
            self.assertEqual(15, len(literals['number']))
            self.assertEqual(6,  len(literals['string']))
            self.assertEqual(2,  len(literals['address']))

            literals = ast.get_literals("BaseTest", only_value=True)
            self.assertEqual(2,  len(literals['string']))

        ast = CombinedJsonParser(f'{contracts_root}/dev/rubic.sol')
        literals = ast.get_literals("Initializable", only_value=True)
        self.assertEqual(1, len(literals['number']))
        self.assertEqual(3, len(literals['string']))

    def test_pc2opcode(self):
        ast = CombinedJsonParser('tests/test_contracts/unchecked.sol')

        self.assertEqual('JUMPI', ast.pc2opcode_by_contract('Test2', False).get(579))
        self.assertEqual('DUP4', ast.pc2opcode_by_contract('Test2', False).get(1163))

    def test_opcode2pcs(self):
        ast = CombinedJsonParser('tests/test_contracts/unchecked.sol')
        expected = {11, 25, 42, 53, 64, 75, 86, 359, 374, 458, 579, 629,
                    712, 826, 844, 852, 959, 1001, 1048, 1090}

        self.assertEqual(expected, ast.opcode2pcs_by_contract('Test2', False).get('JUMPI'))
