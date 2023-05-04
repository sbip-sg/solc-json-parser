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

    def test_literals(self):
        literals = self.parser.get_literals('A', only_value=True)
        expected_numbers = {1, 2, 256, 100, 10 * 10**18}
        self.assertEqual(literals['number'], expected_numbers)


        literals = self.parser.get_literals('B', only_value=True)
        expected_numbers = {10}
        expected_strings = {"myFunction(uint)"}
        self.assertEqual(literals['string'], expected_strings)


    def test_literals(self):
        literals = self.parser.get_literals( 'DirectLoanFixedOfferRedeploy',  only_value=True)
        expected_strings = {'DIRECT_LOAN_FIXED_REDEPLOY'}

        self.assertEqual(literals['string'], expected_strings)

        literals = self.parser.get_literals('ContractKeys',  only_value=True)
        expected_numbers = {32}
        expected_strings = {'AIRDROP_FACTORY',
                            'AIRDROP_FLASH_LOAN',
                            'AIRDROP_RECEIVER',
                            'AirdropWrapper',
                            'LOAN_REGISTRY',
                            'NFTFI_BUNDLER',
                            'NFT_TYPE_REGISTRY',
                            'PERMITTED_AIRDROPS',
                            'PERMITTED_BUNDLE_ERC20S',
                            'PERMITTED_ERC20S',
                            'PERMITTED_NFTS',
                            'PERMITTED_PARTNERS',
                            'PERMITTED_SNFT_RECEIVER',
                            'invalid key'}
        self.assertEqual(literals['number'], expected_numbers)
        self.assertEqual(literals['string'], expected_strings)
