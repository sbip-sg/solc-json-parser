import copy
from semantic_version import Version
import semantic_version
import logging
import addict
import solcx
import json
import os
import re
from typing import Dict, Optional, List, Any, Tuple, Union
from functools import cached_property

try:
    from fields import Field, Function, ContractData, Modifier
    from version_cfg import v_keys
    import consts
except:
    from solc_json_parser.fields import Field, Function, ContractData, Modifier
    from solc_json_parser.version_cfg import v_keys
    import solc_json_parser.consts

SOLC_JSON_AST_FOLDER = "./solc_json_ast"
PARSED_JSON = "./parsed_json"

INSTALLABLE_VERSION = []

INTERFACE_OR_LIB_KIND = set(['interface', 'library'])


def get_by_index(lst: Union[List, Tuple], idx: int):
    '''Get by index from a list, returns None if the index is out of range '''
    if len(lst) > idx:
        return lst[idx]
    return None


def get_in(d, key: Any, *nkeys) -> Any:
    '''Get in nested datastructure by keys. Only dictionary, tuple and
    list are supported'''
    try:
        nd = d.get(key)
    except Exception:
        if type(key) is int:
            nd = get_by_index(d, key)
        else:
            return None
    if len(nkeys) > 0 and nd:
        return get_in(nd, *nkeys)
    return nd


def get_candidates():
    '''
    Returns a cached list of solc versions available for install
    '''
    global INSTALLABLE_VERSION
    if INSTALLABLE_VERSION:
        return INSTALLABLE_VERSION
    else:
        INSTALLABLE_VERSION = sorted(solcx.get_installable_solc_versions())
        return INSTALLABLE_VERSION

def select_available_version(version_str: str, install=False) -> Optional[str]:
    '''Switch to current or the next semantic version available to use. Returns the version selected.'''
    version = Version(version_str)
    candidates = get_candidates()
    try:
        chosen = next(v for v in candidates if v >= version)
    except StopIteration:
        logging.error(f'No candidate version available for {version}')
        return None
    ver = str(chosen)

    if ver and install:
        solc_bin = f'{solcx.get_solcx_install_folder()}/solc-v{ver}'
        if not os.path.exists(solc_bin):
            solcx.install_solc(chosen)

    return ver

def version_str_from_line(line) -> Optional[str]:
    '''
    Extract solc version string from input line
    '''
    if line.strip().startswith('pragma') and 'solidity' in line:
        ver = line.strip().split(maxsplit=2)[-1].split(';', maxsplit=1)[0]
        ver = re.sub(r'([\^>=<~]+)\s+', r'\1', ver)
        return re.sub(r'(\.0+)', '.0', ver)
    return None

def version_str_from_source(source_or_source_file: str) -> Optional[str]:
    inputs = source_or_source_file.split('\n') if '\n' in source_or_source_file else open(source_or_source_file, 'r')

    # Get version part from `pragma solidity ***;` lines
    versions = [version_str_from_line(line) for line in inputs if line.strip().startswith('pragma') and 'solidity' in line]

    if not versions:
        logging.warning('No pragma directive found in source code')
        return None

    return ' '.join(set(versions))

def detect_solc_version(source_or_source_file: str) -> Optional[str]:
    '''
    Detect solc version from a flatten source. Input can be a single file or source code string
    '''
    merged_version = version_str_from_source(source_or_source_file)

    if not merged_version:
        return None

    spec = semantic_version.NpmSpec(merged_version)
    candidates = get_candidates()

    # if we want the best candidate, this normally means higher version
    # ver = spec.select(candidates)

    # if we want the lowest version, will throw if no version matches
    return str(next(spec.filter(candidates)))


def get_line_number_range(start_index:int, offset:int, source_code:str):
    start_line = source_code[:start_index].count('\n') + 1
    end_line   = start_line + source_code[start_index:start_index + offset].count('\n')
    return start_line, end_line

def symbols_to_ids_from_ast_v8(ast: Dict[Any, Any]) -> Dict[str, int]:
    syms = [c['ast']['exportedSymbols'] for c in ast.values()]
    return {k: v[0] for m in syms for k, v in m.items()}

def symbols_to_ids_from_ast_v7(ast: Dict[Any, Any]) -> Dict[str, int]:
    syms = [c['ast']['attributes']['exportedSymbols'] for c in ast.values()]
    return {k: v[0] for m in syms for k, v in m.items()}

class SolidityAst():

    FIELD_VISIBILITY_ALL = frozenset(('default', 'internal', 'public', 'private'))
    FIELD_VISIBILITY_NON_PRIVATE = frozenset(('default', 'internal', 'public'))

    FUNC_VISIBILITY_ALL = frozenset(('external', 'private', 'internal', 'public'))
    FUNC_VISIBILITY_NON_PRIVATE = frozenset(('external', 'internal', 'public'))

    def __init__(self, contract_source_path: str, version=None):
        if '\n' in contract_source_path:
            self.source = contract_source_path
            self.file_path = None
        else:
            self.file_path = contract_source_path
            with open(contract_source_path, 'r') as f:
                self.source = f.read()

        self.exact_version: str   =  version or detect_solc_version(self.source) or consts.DEFAULT_SOLC_VERSION
        self.version_key: str     = self._get_version_key()
        self.keys: addict.Dict    = v_keys[self.version_key]
        self.solc_json_ast: Dict  = self.compile_sol_to_json_ast()
        self.exported_symbols: Dict[str, int] = {} # contract name -> id mapping, to be determined in _parse()
        self.id_to_symbols: Dict[int, str] = {} # reverse mapping of exported_symbols
        self.contracts_dict: Dict = self._parse()

    @cached_property
    def raw_version(self):
        return version_str_from_source(self.source)

    def _get_version_key(self):
        if int(self.exact_version[2]) < 8:
            return f"v{self.exact_version[2]}"
        else:
            return "v8"

    def _get_base_contracts(self, data: List[Dict]) -> List:
        base_contracts = []
        for base_contract in data:
            if base_contract is None: # this is to handle [null] in json
                continue
            base_contracts.append(base_contract['baseName']['referencedDeclaration'])
        return base_contracts

    def _process_function(self, node: Dict) -> Function:
        def _get_signature(function_name, parameters, kind='function') -> str:
            if kind == 'fallback' or kind == 'receive':
                return ''

            signature = "" + function_name + "("
            param_type_str = ""
            if self.version_key == "v8":
                for param in parameters['parameters']:
                    param_type_str += param['typeDescriptions']['typeString'] + ", "
            else:  # v4, v5, v6, v7
                for param in parameters['children']:
                    param_type_str += param['attributes']['type'] + ", "

            param_type_str = param_type_str[:-2] # remove the last ", "
            signature += param_type_str + ")"
            return signature

        def _get_modifiers(node: Dict) -> List[str]:
            modifiers = []
            if self.version_key == "v8":
                for modifier in node['modifiers']:
                    modifiers.append(modifier['modifierName']['name'])
                return modifiers
            else:
                # if None in node['modifiers']:
                #     return []
                # else:
                # if no modifiers, will return []
                for child in node['modifiers']:
                    if get_in(child, 'children', 0, 'attributes', 'type') == "modifier ()":
                        modifiers.append(child['children'][0]['attributes']['value'])
            return modifiers

        # line number range is the same for all versions
        line_number_range_raw = list(map(int, node.get('src').split(':')))
        line_number_range = get_line_number_range(start_index=line_number_range_raw[0], offset=line_number_range_raw[1], source_code=self.source)
        start, offset = line_number_range_raw[0], line_number_range_raw[1]
        raw = self.source[start: start+offset]

        if self.version_key == "v8":
            parameters = node.get('parameters')
            return_type = node.get('returnParameters')
            modifier_nodes = node
        else:  # v4, v5, v6, v7
            parameters  = None
            return_type = None
            for i in range(len(node.get('children'))):
                if node.get('children')[i].get('name') == "ParameterList":
                    parameters  = node.get('children')[i]
                    return_type = node.get('children')[i+1]
                    break

            if node.get("attributes").get("modifiers") is None:
                modifier_nodes = {"modifiers": node.get('children')[2:-1]}
            else:
                modifier_nodes = {"modifiers": []}
            node = node.get("attributes") # get attributes, the structure is different


        assert parameters  is not None
        assert return_type is not None
        visibility = node.get('visibility')
        if node.get('name') is None or node.get('name') == "":
            name = node.get("kind") # for constructor v5, v6, v7, v8
            if not name and node.get("isConstructor"):
                name = "constructor" # for constructor v4

            # anonymous fallback function
            name = name or ''
            # assert name, "Constructor name is None or empty"
        else:
            name = node.get('name') # function name

        inherited_from = ""
        abstract  = not node.get('implemented')
        modifiers = _get_modifiers(modifier_nodes)
        func_kind = node.get('kind')
        state_mutability = node.get('stateMutability')

        signature = _get_signature(name, parameters, func_kind)
        return_signature = _get_signature("", return_type, func_kind)
        return Function(inherited_from=inherited_from, abstract=abstract, visibility=visibility, raw=raw,
                        signature=signature, name=name, return_signature=return_signature, kind=func_kind,
                        modifiers=modifiers, line_num=line_number_range, state_mutability=state_mutability)

    @cached_property
    def v8(self):
        return self.version_key == "v8"
    
    def _process_field(self, node: Dict) -> Field:
        # line number range is the same for all versions
        line_number_range_raw = list(map(int, node.get('src').split(':')))
        line_number_range = get_line_number_range(start_index=line_number_range_raw[0], offset=line_number_range_raw[1], source_code=self.source)

        if self.version_key == "v8":
            pass
        else:  # v4, v5, v6, v7
            node = node.get("attributes")
        visibility = node.get('visibility')
        name = node.get('name')
        inherited_from = ""
        return Field(inherited_from=inherited_from, visibility=visibility, name=name, line_num=line_number_range)

    def _process_modifier(self, node: Dict) -> Modifier:
        if self.version_key == "v8":
            pass
        else:  # v4, v5, v6, v7
            node = node.get("attributes")
        visibility = node.get('visibility')
        name = node.get('name')
        return Modifier(visibility=visibility, name=name)

    def _get_contract_meta_data(self, node: Dict) -> tuple:
        # line number range is the same for all versions
        line_number_range_raw = list(map(int, node.get('src').split(':')))
        line_number_range = get_line_number_range(start_index=line_number_range_raw[0], offset=line_number_range_raw[1], source_code=self.source)
        contract_id = node.get('id')

        if self.version_key == "v8":
            pass  # do nothing
        else:  # v4, v5, v6, v7
            node = node.get("attributes")
            node["abstract"] = not node.get('fullyImplemented')

        assert node.get('name') is not None
        assert node.get('abstract') is not None
        # assert node.get('baseContracts') is not None

        contract_kind = node.get('contractKind')

        is_abstract = node.get('abstract')

        if node.get('baseContracts') is not None:
            base_contracts = self._get_base_contracts(node.get('baseContracts'))
        else:
            base_contracts = node.get('contractDependencies')
        contract_name = node.get('name')

        return contract_id, contract_kind, is_abstract, contract_name, base_contracts, line_number_range

    def _process_contract(self, node: Dict) -> ContractData:
        contract_meta_data = self._get_contract_meta_data(node)
        contract_id, contract_kind, is_abstract, contract_name, base_contracts, line_number_range = contract_meta_data

        functions = []
        fields = []
        modifiers = []
        keys = self.keys
        for node in node.get(keys.children):
            if node[keys.name] == "FunctionDefinition":
                functions.append(self._process_function(node))
            elif node[keys.name] == "VariableDeclaration":
                fields.append(self._process_field(node))
            elif node[keys.name] == "ModifierDefinition":
                modifiers.append(self._process_modifier(node))
            else:
                # not implemented for other types
                pass

        return ContractData(is_abstract, contract_name, contract_kind, base_contracts, fields, functions, modifiers, line_number_range, contract_id)

    def _parse(self) -> Dict:
        def _add_inherited_function_fields(data_dict: Dict[int, ContractData]):
            for contract_id, contract in data_dict.items():
                if len(contract.base_contracts) != 0:
                    for base_contract_id in contract.base_contracts:
                        base_contract = data_dict.get(base_contract_id)
                        base_contract_name = base_contract.name
                        for field in base_contract.fields:
                            new_field = copy.deepcopy(field)
                            new_field.inherited_from = base_contract_name
                            contract.fields.append(new_field)
                        for function in base_contract.functions:
                            new_function = copy.deepcopy(function)
                            new_function.inherited_from = base_contract_name
                            contract.functions.append(new_function)

        # self.save_solc_ast_json("dev")
        # if there are n contracts in the same file, there will be n keys in the json,
        # but we only need the first one[0], because it contains all the contracts, and the rest are the same
        # ast = self.solc_json_ast.get(list(self.solc_json_ast.keys())[0]).get('ast')
        data_dict = {}
        # use version key to get the correct version cfg
        keys = self.keys
        unique_file = set()

        if self.v8:
            self.exported_symbols = symbols_to_ids_from_ast_v8(self.solc_json_ast)
        else:
            self.exported_symbols = symbols_to_ids_from_ast_v7(self.solc_json_ast)

        self.id_to_symbols = {v: k for k, v in self.exported_symbols.items()}

        for ast_key in self.solc_json_ast.keys():
            if ast_key.split(':')[0] in unique_file:
                continue

            unique_file.add(ast_key.split(':')[0])
            ast = self.solc_json_ast.get(ast_key).get('ast')
            if ast[keys.name] != "SourceUnit" or ast[keys.children] is None:
                raise Exception("Invalid AST")

            for i, node in enumerate(ast[keys.children]):
                if node[keys.name] == "PragmaDirective":
                    continue
                elif node[keys.name] == "ContractDefinition":
                    contract = self._process_contract(node)
                    data_dict[contract.contract_id] = contract
                    assert contract.contract_id > 0, 'Missing contract_id in contract'
        _add_inherited_function_fields(data_dict)
        return data_dict

    def _get_exact_version_from_source_code(self, source_code: str) -> Optional[str]:
        if 'pragma solidity' in source_code:
            return source_code.split("pragma solidity")[1]\
                              .split(";")[0].strip()\
                                            .replace('^', '').replace('=', '').replace('>', '').replace('<', '')
        else:
            return None


    def compile_sol_to_json_ast(self) -> dict:
        # print("downloading compiler, version: ", self.exact_version)
        current_working_dir = os.getcwd()
        try:
            solcx.install_solc(self.exact_version)
            solcx.set_solc_version(self.exact_version)
            file_dir = os.path.dirname(self.file_path)
            os.chdir(file_dir)
            ast = solcx.compile_source(self.source, output_values=['ast'], solc_version=self.exact_version)
            return ast
        except Exception as e:
            raise Exception(f"Error: {e}, Please check if the version is valid")
        finally:
            os.chdir(current_working_dir)

    def save_solc_ast_json(self, name: str):
        with open(f'{SOLC_JSON_AST_FOLDER}/{name}_solc_ast.json', 'w') as f:
            json.dump(self.solc_json_ast, f, indent=4)

    def save_parsed_info_json(self, name: str):
        with open(f'{PARSED_JSON}/{name}.json', 'w') as f:
            json.dump(self.contracts_dict, f, default=lambda obj: obj.__dict__, indent=4)


    def all_contracts(self) -> List[ContractData]:
        # dict to list
        return list(self.contracts_dict.values())

    @cached_property
    def all_contract_names(self) -> List[str]:
        return [self.id_to_symbols[d] for d in self.contracts_dict.keys()]

    def all_abstract_contracts(self) -> List[ContractData]:
        return [contract for contract in self.all_contracts() if contract.abstract]

    @cached_property
    def all_abstract_contract_names(self) -> List[str]:
        return [contract.name for contract in self.all_abstract_contracts()]

    @cached_property
    def base_contract_names(self) -> List[str]:
        contracts = self.all_contracts()
        base_contract_ids = set([bc for c in contracts for bc in c.base_contracts])
        names = [self.id_to_symbols[d] for d in base_contract_ids]
        assert len(set(names)) == len(base_contract_ids), f'Possibly different contracts with same name: {self.id_to_symbols} {base_contract_ids}, {names}'
        return names

    def pruned_contracts(self) -> List[ContractData]:
        contracts = self.all_contracts()
        base_contracts_name = self.base_contract_names
        pruned_contracts = [c for c in contracts \
                            if c.name not in base_contracts_name \
                            and c.kind not in INTERFACE_OR_LIB_KIND \
                            and not c.abstract]
        return pruned_contracts

    @cached_property
    def pruned_contract_names(self) -> List[str]:
        return [c.name for c in self.pruned_contracts()]

    def contract_by_name(self, contract_name: str) -> ContractData:
        return self.contracts_dict[self.exported_symbols[contract_name]]

    def fields_in_contract(self, contract: ContractData,
                           name_only: bool = False,
                           field_visibility: Optional[frozenset] = None,
                           parent_field_visibility: Optional[frozenset] = FIELD_VISIBILITY_NON_PRIVATE,
                           with_base_fields=False) -> List[Field]:
        fields = contract.fields
        if (field_visibility is not None) and not (field_visibility == self.FIELD_VISIBILITY_ALL):
            fields = [n for n in fields if n.visibility in field_visibility]

        # contract.fields has already included the base fields
        if not with_base_fields:
            fields = [n for n in fields if n.inherited_from == ''] # remove all base fields
        else:
            temp = []
            for field in fields:
                # fields contains all, so if inherited_from is not '', it is inherited and
                # we need to check the visibility(e.g. sometimes private can not be included here)
                if field.inherited_from != '':
                    if field.visibility in parent_field_visibility:
                        temp.append(field)
                else:
                    temp.append(field)
            # base_contract_names = contract.base_contracts
            # base_fields = [f for c in base_contract_names
            #                for f in self.fields_in_contract_by_name(c, field_visibility=parent_field_visibility)]
            fields = temp

        return [f.name if name_only else f for f in fields]

    def fields_in_contract_by_name(self, contract_name: str,
                                   name_only: bool = False,
                                   field_visibility: Optional[frozenset] = None,
                                   parent_field_visibility: Optional[frozenset] = FIELD_VISIBILITY_NON_PRIVATE,
                                   with_base_fields=False) -> List[Field]:
        contract = self.contract_by_name(contract_name)
        return self.fields_in_contract(contract, name_only, field_visibility, parent_field_visibility, with_base_fields)

    def functions_in_contract(self, contract: ContractData,
                              name_only: bool = False,
                              function_visibility: Optional[frozenset] = None,
                              check_base_contract=True) -> List[Function]:

        # by default, base contract's functions are included
        # different from fields, we don't check parent function visibility
        functions = contract.functions
        if not check_base_contract:
            functions = [n for n in functions if n.inherited_from == '']

        if (function_visibility is not None) and (function_visibility != self.FUNC_VISIBILITY_ALL):
            functions = [n for n in functions if n.visibility in function_visibility]

        if name_only:
            return [n.name for n in functions]
        return functions

    def functions_in_contract_by_name(self, contract_name: str,
                                      name_only: bool = False,
                                      function_visibility: Optional[frozenset] = None,
                                      check_base_contract=True) -> List[Any]:
        # fns = self.contract_by_name(contract_name).functions
        # if check_base_contract:
        #     pass # do nothing
        # else:
        #     fns = [fn for fn in fns if fn.inherited_from == '']
        #
        # if name_only:
        #     return [fn.name for fn in fns]

        contract = self.contract_by_name(contract_name)
        return self.functions_in_contract(contract, name_only, function_visibility, check_base_contract)

    def abstract_function_in_contract_by_name(self, contract_name: str, name_only: bool = False) -> List[Any]:
        # return all abstract functions for a given "contract name"
        fns = [fn for fn in self.functions_in_contract_by_name(contract_name) if fn.abstract]
        if name_only:
            return [fn.name for fn in fns]
        return fns

    def function_by_name(self, contract_name: str, function_name: str) -> Function:
        contract = self.contract_by_name(contract_name)
        funcs    = self.functions_in_contract(contract)
        return next(fn for fn in funcs if fn.name == function_name)

    def all_libraries(self) -> List[ContractData]:
        return [contract for contract in self.all_contracts() if contract.kind == "library"]

    @cached_property
    def all_libraries_names(self) -> List[str]:
        return [lib.name for lib in self.all_libraries()]


if __name__ == '__main__':
    import argparse
    import glob
    import traceback

    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, help="Input file", required=False)
    parser.add_argument('-v', '--verbose', help="Verbose", action='store_true', default=False)
    args = parser.parse_args()

    failed = []
    for c in [args.input] if args.input else glob.glob('contracts/*.sol', recursive=True):
        try:
            print(f'{c} {os.path.exists(c)} {type(c)} {len(c)}')
            ast = SolidityAst(c)
            print(f'{c}: {ast.all_contract_names}')
        except:
            print(f'Testing {c} error')
            failed.append(c)
            if args.verbose:
                traceback.print_exc()

    if not failed:
        print('All contracts parsed success!')
    else:
        print(f'{len(failed)} contracts failed:')
        print(failed)
