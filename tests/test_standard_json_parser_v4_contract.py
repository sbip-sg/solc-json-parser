import unittest
import json
from solc_json_parser.ast_shared import get_in
from solc_json_parser.standard_json_parser import StandardJsonParser


class TestV4Contract(unittest.TestCase):
    def setUp(self):
        main_contract = "TetherToken"
        version = "0.4.26"

        with open('./contracts/standard_json/v4/Tethertoken.solc.0.4.26.input.json', 'r') as f:
            input_json = json.load(f)

        parser = StandardJsonParser(input_json, version)

        self.main_contract = main_contract
        self.parser = parser

    def test_source_by_pc(self):
        tests = [
            # pc or function name -> (line start and end)
            ('removeBlackList', (286, 289),),
            ('transferFrom', (350, 357),),
            (11283, (29, 29),),
            (11096, (17, 17),),
            (6197, (435, 435)),
        ]

        for (fname_or_pc, lines) in tests:
            if type(fname_or_pc)  == str:
                func = self.parser.function_by_name(self.main_contract, fname_or_pc)
                assert lines == tuple(func.line_num), 'Start and end line numbers of the function setRule is not correct'
            else:
                result = self.parser.source_by_pc(self.main_contract, fname_or_pc) or {}
                assert lines ==  tuple(result.get('linenums')), 'Start and end line numbers of the function setRule is not correct'
