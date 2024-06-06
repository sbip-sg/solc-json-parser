# An AST parser for solc json outputs

Parsing AST with solidity source code and get contract information.

## Quickstart

### Installation

Clone this repository and install it with pip:

``` bash
git clone https://github.com/sbip-sg/solc-json-parser.git
cd solc-json-parser
pip install .
```

### Usage

Example usage using [standard json](https://docs.soliditylang.org/en/v0.8.17/using-the-compiler.html#compiler-input-and-output-json-description):

``` python
import json
from solc_json_parser.standard_json_parser import StandardJsonParser
with open('contracts/standard_json/75b8.standard-input.json') as f:
    input_json = json.load(f)

version = '0.8.4'
parser = StandardJsonParser(input_json, version)

# Get all contract names
parser.all_contract_names
# ['IERC1271',
#  ...
#  'ContractKeys',
#  'NFTfiSigningUtils',
#  'NftReceiver',
#  'Ownable']

# Get source code by PC
source = parser.source_by_pc('DirectLoanFixedOffer', 13232)
source
# {'pc': 13232,
#  'linenums': [921, 924],
#  'fragment': 'LoanChecksAndCalculations.computeRevenueShare(\n            adminFee,\n            loanExtras.revenueShareInBasisPoints\n        )',
#  'fid': 'contracts/loans/direct/loanTypes/DirectLoanBaseMinimal.sol',
#  'begin': 45007,
#  'end': 45134,
#  'source_idx': 26,
#  'source_path': 'contracts/loans/direct/loanTypes/DirectLoanBaseMinimal.sol'}

# Get function AST unit by PC
func = parser.function_unit_by_pc('DirectLoanFixedOffer', 13232)
# Parameter names of this function
[n.get('name') for n in func.get('parameters').get('parameters')]
# ['_loanId', '_borrower', '_lender', '_loan']
# Function selector, available only for external or public functions
func.get('functionSelector')

# Get the innermost AST unit by PC
parser.ast_unit_by_pc('DirectLoanFixedOffer', 13232)
```

## Command line tools

``` bash
solc-json-parser --help
```

Decode binary to opcodes:

``` bash
❯ solc-json-parser dp 0x60806040525f80fdfea26469706673582212200466fd4ed0d73499199c39545f7019da158defa354cc0051afe02754ec8e32b464736f6c63430008180033
PUSH1 0x80
PUSH1 0x40
MSTORE
PUSH0 0x
DUP1
REVERT
INVALID
LOG2
PUSH5 0x6970667358
0X22
SLT
SHA3
DIV
PUSH7 0xfd4ed0d7349919
SWAP13
...
```



## Note

- This library only supports detecting Solidity version newer than or equal to
  `v0.4.11`. This is due to the limitation of the base library [py-solc-x](https://solcx.readthedocs.io/en/latest/).
