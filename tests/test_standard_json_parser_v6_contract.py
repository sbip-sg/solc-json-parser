import unittest
import json
from solc_json_parser.ast_shared import get_in
from solc_json_parser.standard_json_parser import StandardJsonParser


class TestV6Contract(unittest.TestCase):
    def setUp(self):
        main_contract = "MaskToken"
        version = "0.6.6"

        with open('./contracts/standard_json/v6/MaskToken.solc.0.6.6.input.json', 'r') as f:
            input_json = json.load(f)

        parser = StandardJsonParser(input_json, version)

        self.main_contract = main_contract
        self.parser = parser


    def test_source_by_pc(self):
        tests = [
            (3012, (538, 538),),
            (3698, (284, 284),),
        ]

        for (fname_or_pc, lines) in tests:
            result = self.parser.source_by_pc(self.main_contract, fname_or_pc) or {}
            assert lines ==  tuple(result.get('linenums')), 'Start and end line numbers of the function setRule is not correct'

    def test_function_by_name(self):
        tests = [
            ('approve', (463, 466),),
            ('_approve', (601, 607),),
        ]

        for (fname, lines) in tests:
            func = self.parser.function_by_name(self.main_contract, fname)
            assert lines ==  tuple(func.line_num), 'Start and end line numbers of the function setRule is not correct'


    def test_function_ast_unit_by_pc(self):
        tests = [
            ('_transfer', 3012,),
            ('sub', 3698,),
        ]

        for (fname, pc) in tests:
            result = self.parser.function_unit_by_pc(self.main_contract, pc) or {}
            assert fname ==  result.get('name'), 'Function name is not correct'

    def test_ast_unit_by_pc(self):
        tests = [
            ('address', ['commonType', 'typeString'], 3012,),
            ('bool', ['typeDescriptions', 'typeString'], 3698,),
        ]

        for (fname, keys, pc) in tests:
            result = self.parser.ast_unit_by_pc(self.main_contract, pc) or {}
            val = result
            source = self.parser.source_by_pc(self.main_contract, pc)
            for k in keys:
                val = val.get(k)
            assert fname ==  val, f'Unexpected unit found, ast unit: {result} source: {source}'
