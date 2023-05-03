import unittest
import json
import re
from solc_json_parser.standard_json_parser import StandardJsonParser

contracts_root = './contracts/standard_json/'

class TestStandardJsonParser(unittest.TestCase):
    def setUp(self):
        files = ['a.sol', 'b.sol', 'main.sol']
        ver = '0.7.0'
        self.main_contract = 'Main'
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
        self.parser = parser

    def test_standard_json_source_mapping(self):
        expected_data = [
            {'pc': 427, 'linenums': [10, 10], 'begin': 166, 'end': 176, 'source_path': 'b.sol'},
            {'pc': 800, 'linenums': [9, 9], 'begin': 224, 'end': 239, 'source_path': 'a.sol'},
            {'pc': 850, 'linenums': [11, 11], 'begin': 289, 'end': 302, 'source_path': 'a.sol'},
            {'pc': 869, 'linenums': [11, 11], 'begin': 210, 'end': 225, 'source_path': 'main.sol'},
        ]

        for expected in expected_data:
            pc = expected['pc']
            keys = expected.keys()
            actual = self.parser.source_by_pc(self.main_contract, pc, False)
            e = { k: actual[k] for k in keys }

            self.assertEqual(e, expected)


    def test_all_contract_name(self):
        expected_contract_names = {'A', 'B', 'Main'}
        all_contract_names = set(self.parser.all_contract_names)
        self.assertEqual(expected_contract_names, all_contract_names, 'Contracts should be identified correctly')

    def test_base_contract_names(self):
        expected_base_contract_names = {'A', 'B'}
        base_contract_names = set(self.parser.base_contract_names)
        self.assertEqual(expected_base_contract_names, base_contract_names, 'Base contracts should be identified correctly')

    def test_pruned_contract_names(self):
        expected_pruned_contract_names = {'Main'}
        pruned_contract_names = set(self.parser.pruned_contract_names)
        self.assertEqual(expected_pruned_contract_names, pruned_contract_names, 'Pruned contracts should be identified correctly')
