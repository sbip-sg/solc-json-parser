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
ast.all_contract_names()
```

Flatten source code:

``` bash
from solc_json_parser.flatten import FlattenSolidity

# Pass the main contract to be flattened
fl = FlattenSolidity('contracts/funpass/01_13_FunPassAlpha.sol')

# Get the flattened source code
fl.flatten_source

# Reverse look up the location from the line number in the flattend source code
fl.reverse_line_lookup(223)

# Returns a tuple containing original file path, linenumber and the line:
# ('./contracts/complex/11_13_IERC1155Receiver.sol',
# 53,
# '        uint256[] calldata ids,\n')
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

