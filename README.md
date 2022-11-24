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
```

