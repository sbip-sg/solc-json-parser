# A solc json parser 

## Requirements

- Python 3.9 
- Pip 
- Required libraries can be installed with

```bash
pip install -r requirements.txt
```

## Usage 

Parsing AST with solidity source code and get contract information:

``` python
from solc_json_parser.parser import SolidityAst

# The input can be a file path or source code
ast = SolidityAst('contracts/BlackScholesEstimate_8.sol')
ast.all_contract_names

# Get source code by program counter
ast.source_by_pc('BlackScholesEstimate', 92)
```

## Test

``` bash
python -m unittest -v
# or
python setup.py pytest
```

## Install 

Install for development:

``` bash
pip install -e .
```


Or install from github:

``` bash
pip install https://github.com/sbip-sg/solc-json-parser/archive/main.zip
```

