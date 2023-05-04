import unittest
import json
from solc_json_parser.abi import abi_from_binary

class TestAbiFromBinary(unittest.TestCase):
    def test_abi_from_binary(self):
        with open('./tests/test_contracts/rubic.bin', 'r') as f:
            binary = f.read()

        sigs = abi_from_binary(binary)
        with open('tests/test_contracts/rubic.hashes.json', 'r') as f:
            expected_sigs = json.loads(f.read())

        print(f'sigs: {sigs}')

        expected_fn_by_sig = {v: k for k, v in expected_sigs.items()}

        found = set(expected_sigs.values()).intersection(sigs)
        missing = set(expected_sigs.values()).difference(sigs)

        print('*' * 40)
        print(f'Found sigs: {found}')
        for hsh in found:
            print(f'  {hsh}: {expected_fn_by_sig.get(hsh)}')

        print('*' * 40)
        print(f'Missing sigs: {missing}')
        for hsh in missing:
            print(f'  {hsh}: {expected_fn_by_sig.get(hsh)}')

        self.assertEqual(sigs, set(expected_sigs.values()))
