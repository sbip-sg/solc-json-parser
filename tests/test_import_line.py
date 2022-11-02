import unittest
from solc_json_parser.fix_imports import sol_in_line, to_simple_name

class TestFixImport(unittest.TestCase):
    def test_sol_in_line(self):
        tests = [
            ('import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";', '@openzeppelin/contracts/token/ERC1155/ERC1155.sol'),
            ('import "filename.sol";', 'filename.sol'),
            ('import * as symbolName from "filename.sol";', 'filename.sol'),
            ('import "filename.sol" as symbolName;', 'filename.sol'),
            ('import {symbol1 as alias, symbol2} from "filename.sol";', 'filename.sol'),
            ('import {EnumerableSet, ERC1155EnumerableStorage} from "@solidstate/contracts/token/ERC1155/enumerable/ERC1155EnumerableStorage.sol";', '@solidstate/contracts/token/ERC1155/enumerable/ERC1155EnumerableStorage.sol')
        ]
        for (line, expected) in tests:
            self.assertEqual(expected, sol_in_line(line), f'Failed for {line}')

    def test_to_simple_name(self):
        tests = [
            ('@openzeppelin/contracts/token/ERC1155/ERC1155.sol', 'ERC1155.sol'),
            ('@solidstate/contracts/token/ERC1155/enumerable/ERC1155EnumerableStorage.sol', 'ERC1155EnumerableStorage.sol')
        ]

        for (line, expected) in tests:
            self.assertEqual(expected, to_simple_name(line))
