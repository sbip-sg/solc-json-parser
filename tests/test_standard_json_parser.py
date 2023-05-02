import unittest
import json
import re
from solc_json_parser.standard_json_parser import StandardJsonParser

contracts_root = './contracts/standard_json/'

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


class TestStandardJsonParser(unittest.TestCase):
    def test_standard_json_multi_files(self):
        files = ['a.sol', 'b.sol', 'main.sol']
        ver = '0.7.0'
        main_contract = 'Main'
        sources = {}
        for file in files:
            with open(contracts_root + file, 'r') as f:
                sources[file] = {'content': f.read()}

        input_json = {
            'language': 'Solidity',
            'sources': sources,
            'settings': {
                'optimizer': {
                    'enabled': False,
                },
                'evmVersion': 'istanbul',
                'outputSelection': {
                    '*': {
                        '*': [ '*' ],
                        '': ['ast']
                    }
                }
            }
        }

        parser = StandardJsonParser(input_json, ver)

        expected_data = [
            {'pc': 427, 'linenums': [10, 10], 'begin': 166, 'end': 176, 'source_path': 'b.sol'},
            {'pc': 800, 'linenums': [9, 9], 'begin': 224, 'end': 239, 'source_path': 'a.sol'},
            {'pc': 850, 'linenums': [11, 11], 'begin': 289, 'end': 302, 'source_path': 'a.sol'},
            {'pc': 869, 'linenums': [11, 11], 'begin': 210, 'end': 225, 'source_path': 'main.sol'},
        ]

        for expected in expected_data:
            pc = expected['pc']
            keys = expected.keys()
            actual = parser.source_by_pc(main_contract, pc, False)
            e = { k: actual[k] for k in keys }

            self.assertEqual(e, expected)
