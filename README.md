# An AST parser for solc json outputs

Parsing AST with solidity source code and get contract information.

## Installation

Clone this repository and install it with pip:

``` bash
pip install .
```

## Usage

Using combined json, support for contract with multiple source files is limited:

``` python
from solc_json_parser.combined_json_parser import CombinedJsonParser

# The input can be a file path or source code
parser = CombinedJsonParser('contracts/BlackScholesEstimate_8.sol')
parser.all_contract_names

# List all functions in contract
parser.functions_in_contract_by_name('BlackScholesEstimate', name_only=True)

# Get source code by program counter
parser.source_by_pc('BlackScholesEstimate', 92)
{'pc': 92,
 'fragment': 'function retBasedBlackScholesEstimate(\n        uint256[] memory _numbers,\n        uint256 _underlying,\n        uint256 _time\n    ) public pure {\n        uint _vol = stddev(_numbers);\n        blackScholesEstimate(_vol, _underlying, _time);\n    }',
 'begin': 2633,
 'end': 2877,
 'linenums': (69, 76),
 'source_idx': 0,
 'source_path': 'BlackScholesEstimate_8.sol'}


# Get deployment code by contract name
parser.get_deploy_bin_by_contract_name('BlackScholesEstimate')

# Get literal values by contract name
parser.get_literals('BlackScholesEstimate', True)
{'number': {0, 1, 2, 40}, 'string': set(), 'address': set(), 'other': set()}
```

Using [standard json](https://docs.soliditylang.org/en/v0.8.17/using-the-compiler.html#compiler-input-and-output-json-description):

``` python
import json
from solc_json_parser.standard_json_parser import StandardJsonParser
with open('contracts/standard_json/75b8.standard-input.json') as f:
    input_json = json.load(f)

version = '0.8.4'
parser = StandardJsonParser(input_json, version)

# Other usages are the same as combined json parser
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
