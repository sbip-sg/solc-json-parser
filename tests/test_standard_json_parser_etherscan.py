import unittest
import json
import re
from solc_json_parser.standard_json_parser import StandardJsonParser

# Version pattern used in the etherscan api response
version_pattern = r'v(\d+\.\d+\.\d+)'

def simplify_version(s):
    match = re.search(version_pattern, s or '')
    if match:
        extracted_version = match.group(1)
        return extracted_version
    else:
        return None

def parse_etherscan_json(input: str, as_path: bool = False):
    '''
    Parse contract json file from etherscan API
    '''
    if as_path:
        with open(input, 'r') as f:
            input = f.read()
    try:
        return json.loads(input)
    except Exception:
        return None


OUTPUT_SELECT_ALL = {'*': {'*': [ '*' ], '': ['ast']}}

class TestStandardJsonParser(unittest.TestCase):
    def setUp(self):
        result = parse_etherscan_json('./contracts/standard_json/0x8252Df1d8b29057d1Afe3062bf5a64D503152BC8.etherscan.json', True)
        version = simplify_version(result['CompilerVersion'])
        main_contract = result['ContractName']
        implementation = result['Implementation']

        input_json = json.loads(result['SourceCode'][1:][:-1])

        input_json['settings']['outputSelection'] = OUTPUT_SELECT_ALL
        parser = StandardJsonParser(input_json, version)

        self.maxDiff = None

        self.main_contract = main_contract
        self.implementation = implementation
        self.parser = parser

    def test_deployment_binary(self):
        print(f'main_contract: {self.main_contract}')
        with open('./contracts/standard_json/0x8252Df1d8b29057d1Afe3062bf5a64D503152BC8.deployment.bin') as f:
            expected = f.read()

        _filename, _contract_name, bin = self.parser.get_deployment_binary(self.main_contract)[0]
        self.assertIsNotNone(bin)
        self.assertEqual(bin, expected)

    def test_contract_names(self):
        self.assertEqual(self.parser.pruned_contract_names, [self.main_contract])

        self.assertSetEqual(set(self.parser.all_libraries_names), {'SafeERC20', 'Address', 'Strings', 'ECDSA', 'SignatureChecker', 'LoanAirdropUtils', 'LoanChecksAndCalculations', 'ContractKeys', 'NFTfiSigningUtils'})

        self.assertSetEqual(set(self.parser.all_abstract_contract_names), {'Pausable', 'ReentrancyGuard', 'Context', 'BaseLoan', 'DirectLoanBaseMinimal', 'NftReceiver', 'Ownable'})


    def test_events(self):
        events = [e.name for e in self.parser.events_in_contract_by_name('Ownable')]
        expected = ['OwnershipTransferred']
        self.assertListEqual(events, expected)




    # def test_standard_json_source_mapping(self):
    #     expected_data = [
    #         {'pc': 427, 'linenums': [10, 10], 'begin': 166, 'end': 176, 'source_path': 'b.sol'},
    #         {'pc': 800, 'linenums': [9, 9], 'begin': 224, 'end': 239, 'source_path': 'a.sol'},
    #         {'pc': 850, 'linenums': [11, 11], 'begin': 289, 'end': 302, 'source_path': 'a.sol'},
    #         {'pc': 869, 'linenums': [11, 11], 'begin': 210, 'end': 225, 'source_path': 'main.sol'},
    #     ]

    #     for expected in expected_data:
    #         pc = expected['pc']
    #         keys = expected.keys()
    #         actual = self.parser.source_by_pc(self.main_contract, pc, False)
    #         e = { k: actual[k] for k in keys }

    #         self.assertEqual(e, expected)


    # def test_all_contract_name(self):
    #     expected_contract_names = {'A', 'B', 'Main'}
    #     all_contract_names = set(self.parser.all_contract_names)
    #     self.assertEqual(expected_contract_names, all_contract_names, 'Contracts should be identified correctly')

    # def test_base_contract_names(self):
    #     expected_base_contract_names = {'A', 'B'}
    #     base_contract_names = set(self.parser.base_contract_names)
    #     self.assertEqual(expected_base_contract_names, base_contract_names, 'Base contracts should be identified correctly')

    # def test_pruned_contract_names(self):
    #     expected_pruned_contract_names = {'Main'}
    #     pruned_contract_names = set(self.parser.pruned_contract_names)
    #     self.assertEqual(expected_pruned_contract_names, pruned_contract_names, 'Pruned contracts should be identified correctly')
