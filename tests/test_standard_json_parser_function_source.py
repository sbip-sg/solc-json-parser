import unittest
import json
import re
from solc_json_parser.standard_json_parser import StandardJsonParser

OUTPUT_SELECT_ALL = {'*': {'*': [ '*' ], '': ['ast']}}

class TestFunctionSourceByStandardJsonParser(unittest.TestCase):
    def setUp(self):
        main_contract = "PepeToken"
        version = "0.8.0"

        with open('./contracts/standard_json/pepe_single_source_flattened.solc.json', 'r') as f:
            input_json = json.load(f)

        parser = StandardJsonParser(input_json, version)

        self.main_contract = main_contract
        self.parser = parser


    def test_source_by_function_name(self):
        tests = [('setRule', (652, 662),),
                 ('transferFrom', (403, 420),),]

        for (fname, lines) in tests:
            func = self.parser.function_by_name('PepeToken', fname)
            assert lines ==  func.line_num, 'Start and end line numbers of the function setRule is not correct'
