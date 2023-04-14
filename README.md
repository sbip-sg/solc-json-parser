# An AST parser for solc json outputs

## Usage

Parsing AST with solidity source code and get contract information:

``` python
from solc_json_parser.parser import SolidityAst

# The input can be a file path or source code
ast = SolidityAst('contracts/BlackScholesEstimate_8.sol')
ast.all_contract_names

# List all functions in contract
ast.functions_in_contract_by_name('BlackScholesEstimate', name_only=True)

# Get source code by program counter
ast.source_by_pc('BlackScholesEstimate', 92)

# Get deployment code by contract name
ast.get_deploy_bin_by_contract_name('BlackScholesEstimate')
```

## Note

- This library only supports detecting Solidity version newer than or equal to
  `v0.4.11`. This is due to the limitation of the base library [py-solc-x](https://solcx.readthedocs.io/en/latest/).
