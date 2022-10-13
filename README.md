# A solc json parser 

## Requirements

- Python 3.9 
- Pip 
- Required libraries can be installed with

```bash
pip install -r requirements.txt
```

## Usage 

``` python
from solc_json_parser.parser import SolidityAst
ast = SolidityAst
ast.all_contract_names()
```

## Test

``` bash
python -m unittest -v
# or
python setup.py pytest
```

## Install 

``` bash
pip install -e .
```

