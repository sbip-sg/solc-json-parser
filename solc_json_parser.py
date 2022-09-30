import argparse
import copy
import solcx
import json
from fields import Field, Function, ContractData, Modifier
from version_cfg import v_keys
SOLC_JSON_AST_FOLDER = "./solc_json_ast"
PARSED_JSON = "./parsed_json"
 
def get_version_key(version):
    print(version)
    if int(version[2]) < 8:
        return f"v{version[2]}"
    else:
        return "v8"


def save_solc_ast(out, name):
    with open(f'./{SOLC_JSON_AST_FOLDER}/{name}_solc_ast.json', 'w') as f:
        json.dump(out, f, indent=4)
def compile_to_json(source_code_path):
    
    def _get_version(source_code):
        return source_code.split("pragma solidity")[1].split(";")[0].strip().replace('^', '').replace('=','')
    
    def _get_source_code(source_code_path):
        # gettting source code from file
        with open(source_code_path, "r") as f:
            source = f.read()
        return source

    source_code = _get_source_code(source_code_path)
    # print(source_code)
    version = _get_version(source_code)
    print("downloading compiler, version: ", version)
    solcx.install_solc(version)
    solcx.set_solc_version(version)
    out = solcx.compile_source(source_code, output_values=['ast'], solc_version=version)
    return out, version

def get_base_contracts(data):
    base_contracts = []
    for base_contract in data:
        if base_contract is None:
            continue
        base_contracts.append(base_contract['baseName']['name'])
    return base_contracts


def process_function(node, version_key):
    def _get_signature(function_name, parameters, version_key):
        signature = "" + function_name + "("
        param_type_str = ""
        if version_key == "v8":
            for param in parameters['parameters']:
                param_type_str += param['typeDescriptions']['typeString'] + ", "
        else: #v4, v5, v6, v7
            for param in parameters['children']:
                param_type_str += param['attributes']['type'] + ", "
        
        param_type_str = param_type_str[:-2]
        signature += param_type_str + ")"
        return signature
    
    def _get_modifiers(node, version_key):
        modifiers = []
        if version_key == "v8":
            for modifier in node['modifiers']:
                modifiers.append(modifier['modifierName']['name'])
            return modifiers
        else:
            if None in node['modifiers']:
                return []
            else:
                for child in node['modifiers']:
                    if child['children'][0]['attributes']['type'] == "modifier ()":
                        modifiers.append(child['children'][0]['attributes']['value'])
        return modifiers
        
    if version_key == "v8":
        parameters  = node.get('parameters')
        return_type = node.get('returnParameters')
        modifier_nodes = node
    else: #v4, v5, v6, v7
        parameters  = node.get('children')[0]
        return_type = node.get('children')[1]
        if node.get("attributes").get("modifiers") is None:
            modifier_nodes = {"modifiers": node.get('children')[2:-1]}
        else:
            modifier_nodes = {"modifiers": [None]}
        node = node.get("attributes")
        
        
    
    visibility = node.get('visibility')
    if node.get('name') is None or node.get('name') == "":
        name = node.get("kind")
    else:
        name = node.get('name')
    
    inherited_from = ""
    abstract  = not node.get('implemented')
    modifiers = _get_modifiers(modifier_nodes, version_key)
    
    
    signature        = _get_signature(name, parameters,  version_key)
    return_signature = _get_signature("",   return_type, version_key)
    return Function(inherited_from=inherited_from, abstract=abstract, visibility=visibility,
                    signature=signature, name=name, return_signature=return_signature, modifiers=modifiers)

    

def process_field(node, version_key):
    if version_key == "v8":
            pass
    else: #v4, v5, v6, v7
        node = node.get("attributes")
    visibility = node.get('visibility')
    name = node.get('name')
    inherited_from = ""

    return Field(inherited_from=inherited_from, visibility=visibility, name=name)
    

def process_modifier(node, version_key):
    if version_key == "v8":
        pass
    else: #v4, v5, v6, v7
        node = node.get("attributes")
    
    visibility = node.get('visibility')
    name = node.get('name')
    return Modifier(visibility=visibility, name=name)


def get_contract_meta_data(node, version_key):
    if version_key == "v8":
        pass #do nothing
    else: #v4, v5, v6, v7
        node = node.get("attributes")
        node["abstract"] = not node.get('fullyImplemented')
    
    if node.get('contractKind') == None:
        pass
    contract_kind = node.get('contractKind')

    if node.get('abstract') == None:
        pass
    is_abstract = node.get('abstract')

    if node.get('baseContracts') == None:
        pass
    base_contracts = get_base_contracts(node.get('baseContracts'))

    contract_name = node.get('name')
    
    return contract_kind, is_abstract, contract_name, base_contracts
    
    

def process_contract(node, version_key):
    keys = v_keys[version_key]
    
    contract_meta_data = get_contract_meta_data(node, version_key)
    contract_kind, is_abstract, contract_name, base_contracts = contract_meta_data
    
    
    functions = []
    fields    = []
    modifiers = []
    for node in node.get(keys.children):
        if node[keys.name] == "FunctionDefinition":
            functions.append(process_function(node, version_key))
        elif node[keys.name] == "VariableDeclaration":
            fields.append(process_field(node, version_key))
        elif node[keys.name] == "ModifierDefinition":
            modifiers.append(process_modifier(node, version_key))
        else:
            # not implemented for other types
            pass
    
    contract_data = ContractData(is_abstract, contract_name, contract_kind, base_contracts, fields, functions, modifiers)
    return contract_data

def parse(solc_json_ast:dict, version, filename:str):
    
    def _add_inherited_function_fields(data_dict: dict):
        for contract_name, contract in data_dict.items():
            if len(contract.base_contracts) != 0:
                for base_contract_name in contract.base_contracts:
                    base_contract = data_dict[base_contract_name]
                    for field in base_contract.fields:
                        new_field = copy.deepcopy(field)
                        new_field.inherited_from = base_contract_name
                        contract.fields.append(new_field)
                    for function in base_contract.functions:
                        new_function = copy.deepcopy(function)
                        new_function.inherited_from = base_contract_name
                        contract.functions.append(new_function)
    
    def _save_info_json(data_dict ,filename):
        with open(f'./{PARSED_JSON}/{filename}.json', 'w') as f:
            json.dump(data_dict, f, default=lambda obj: obj.__dict__, indent=4)
            
    
    ast = solc_json_ast.get(list(solc_json_ast.keys())[0]).get('ast')
    data_dict = {}
    version_key = get_version_key(version)
    print("version key: ", version_key)
    keys = v_keys[version_key]
    
    if ast[keys.name] != "SourceUnit" or ast[keys.children] is None:
        raise Exception("Invalid AST")
    
    for i, node in enumerate(ast[keys.children]):
        if node[keys.name] == "PragmaDirective":
            continue
        elif node[keys.name] == "ContractDefinition":
            contract = process_contract(node, version_key)
            data_dict[contract.name] = contract
            
    _add_inherited_function_fields(data_dict)
    _save_info_json(data_dict, filename)

################################################################################
# 1. the following methods need to be implemented, you can take reference from https://verazt.slack.com/files/U0405RJUNLD/F0423LMJF5Z/solidity_ast.py
# ./solidity_ast.py:62:    def all_contracts(self) -> List[Node]:
# ./solidity_ast.py:74:    def all_abstract_contracts(self) -> List[Node]:
# ./solidity_ast.py:81:    def get_version(unit) -> str:
# ./solidity_ast.py:105:    def base_contracts_names(self) -> List[str]:
# ./solidity_ast.py:115:    def pruned_contracts(self) -> List[Node]:
# ./solidity_ast.py:126:    def pruned_contract_names(self) -> List[str]:
# ./solidity_ast.py:129:    def fields_in_contract(self,
# ./solidity_ast.py:161:    def contract_by_name(self, contract_name: str) -> Node:
# ./solidity_ast.py:167:    def fields_in_contract_by_name(self, contract_name: str, name_only: bool = False, field_visibility: Optional[frozenset] = None,  parent_field_visibility: Optional[frozenset] = FIELD_VISIBILITY_NON_PRIVATE):
# ./solidity_ast.py:172:    def functions_in_contract(self, contract: Node, name_only: bool = False, function_visibility: Optional[frozenset] = None, check_base_contract=True):
# ./solidity_ast.py:193:    def functions_in_contract_by_name(self, contract_name: str, name_only: bool = False) -> List[Any]:
# ./solidity_ast.py:198:    def abstract_functions_in_contract_by_name(self, contract_name: str, name_only: bool = False) -> List[Any]:
# ./solidity_ast.py:211:    def function_by_name(self, contract_name: str, function_name: str):
# ./solidity_ast.py:216:    def get_all_literals(self):
# ./solidity_ast.py:236:    def get_all_address(self):
# ./solidity_ast.py:241:    def get_fallback_functions(self, contract_name: str):
# 2. please consider using class if necessary
# 3. consider adding test cases in `tests/test_parser.py`
# 4. either define necessary data structure (with data class, type
#    hint (https://docs.python.org/3/library/typing.html) for example)
#    or add documentation and/or example data indicating the expected
#    input and output.


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="path to source code", default="./contracts/whole.sol")
    args = parser.parse_args()
    path = args.path
    
    filename = path.split("/")[-1].split(".")[0]
    print("parsing filename: " + filename)
    solc_json_ast, version = compile_to_json(path)
    
    print("saving solc_json_ast to folder: " + SOLC_JSON_AST_FOLDER)
    save_solc_ast(solc_json_ast, filename)
    
    print("parse solc_json_ast to get info")
    parse(solc_json_ast, version, filename)
    
    print("parsing done")
    
