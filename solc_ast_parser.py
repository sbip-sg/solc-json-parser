import argparse
import copy

import addict
import solcx
import json
import os
from typing import Dict, Optional, List, Any, Tuple
from functools import cached_property, cache
from fields import Field, Function, ContractData, Modifier
from version_cfg import v_keys

SOLC_JSON_AST_FOLDER = "./solc_json_ast"
PARSED_JSON = "./parsed_json"

class SolidityAST():

    FIELD_VISIBILITY_ALL = frozenset(('default', 'internal', 'public', 'private'))
    FIELD_VISIBILITY_NON_PRIVATE = frozenset(('default', 'internal', 'public'))

    FUNC_VISIBILITY_ALL = frozenset(('external', 'private', 'internal', 'public'))
    FUNC_VISIBILITY_NON_PRIVATE = frozenset(('external', 'internal', 'public'))

    def __init__(self, contract_source_path: str):
        self.contract_source_path: str = contract_source_path
        self._source_code: str    = self._get_source_code()
        self.version: str         = self._get_version_from_source_code(self._source_code)
        self.version_key: str     = self._get_version_key()
        self.keys: addict.Dict    = v_keys[self.version_key]
        self.solc_json_ast: Dict  = self.compile_sol_to_json_ast()

        # self.save_solc_ast_json(os.path.basename(self.contract_source_path))

        self.exported_symbols = None # to be determined in _parse()
        self.contracts_dict: Dict = self._parse()

    def _get_version_key(self):
        if int(self.version[2]) < 8:
            return f"v{self.version[2]}"
        else:
            return "v8"

    def _get_base_contracts(self, data: List[Dict]) -> List:
        base_contracts = []
        for base_contract in data:
            if base_contract is None: # this is to handle [null] in json
                continue
            base_contracts.append(base_contract['baseName']['name'])
        return base_contracts

    def _process_function(self, node: Dict) -> Function:
        def _get_signature(function_name, parameters) -> str:
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
                    if child['children'][0]['attributes']['type'] == "modifier ()":
                        modifiers.append(child['children'][0]['attributes']['value'])
            return modifiers

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


        assert parameters is not None
        assert return_type is not None
        visibility = node.get('visibility')
        if node.get('name') is None or node.get('name') == "":
            name = node.get("kind") # for constructor
        else:
            name = node.get('name') # function name

        inherited_from = ""
        abstract = not node.get('implemented')
        modifiers = _get_modifiers(modifier_nodes)

        signature = _get_signature(name, parameters)
        return_signature = _get_signature("", return_type)
        return Function(inherited_from=inherited_from, abstract=abstract, visibility=visibility,
                        signature=signature, name=name, return_signature=return_signature, modifiers=modifiers)

    def _process_field(self, node: Dict) -> Field:
        if self.version_key == "v8":
            pass
        else:  # v4, v5, v6, v7
            node = node.get("attributes")
        visibility = node.get('visibility')
        name = node.get('name')
        inherited_from = ""
        return Field(inherited_from=inherited_from, visibility=visibility, name=name)

    def _process_modifier(self, node: Dict) -> Modifier:
        if self.version_key == "v8":
            pass
        else:  # v4, v5, v6, v7
            node = node.get("attributes")
        visibility = node.get('visibility')
        name = node.get('name')
        return Modifier(visibility=visibility, name=name)

    def _get_contract_meta_data(self, node: Dict) -> tuple:
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
            contract_dependencies = node.get('contractDependencies')
            contract_name_to_id = self.exported_symbols
            id_to_contract_name = {v[0]: k for k, v in contract_name_to_id.items()}
            base_contracts = [id_to_contract_name[contract_id] for contract_id in contract_dependencies]
        contract_name = node.get('name')

        return contract_kind, is_abstract, contract_name, base_contracts

    def _process_contract(self, node: Dict) -> ContractData:
        contract_meta_data = self._get_contract_meta_data(node)
        contract_kind, is_abstract, contract_name, base_contracts = contract_meta_data

        functions = []
        fields = []
        modifiers = []
        keys = self.keys
        for node in node.get(keys.children):
            if node[keys.name] == "FunctionDefinition":
                functions.append(self._process_function(node))
                # print(functions)
            elif node[keys.name] == "VariableDeclaration":
                fields.append(self._process_field(node))
            elif node[keys.name] == "ModifierDefinition":
                modifiers.append(self._process_modifier(node))
            else:
                # not implemented for other types
                pass

        return ContractData(is_abstract, contract_name, contract_kind, base_contracts, fields, functions, modifiers)

    def set_exported_symbols(self, ast):
        if self.version_key == "v8":
            pass
        else:  # v4, v5, v6, v7
            self.exported_symbols = ast.get("attributes").get("exportedSymbols")

    def _parse(self) -> Dict:
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

        # if there are n contracts in the same file, there will be n keys in the json,
        # but we only need the first one[0], because it contains all the contracts, and the rest are the same
        ast = self.solc_json_ast.get(list(self.solc_json_ast.keys())[0]).get('ast')
        self.set_exported_symbols(ast)
        data_dict = {}

        # use version key to get the correct version cfg
        keys = self.keys

        if ast[keys.name] != "SourceUnit" or ast[keys.children] is None:
            raise Exception("Invalid AST")

        for i, node in enumerate(ast[keys.children]):
            if node[keys.name] == "PragmaDirective":
                continue
            elif node[keys.name] == "ContractDefinition":
                contract = self._process_contract(node)
                data_dict[contract.name] = contract
                # print(contract.name)

        _add_inherited_function_fields(data_dict)

        # basename = os.path.basename(self.contract_source_path)
        # self.save_solc_ast_json(basename)
        return data_dict

    def _get_source_code(self) -> str:
        with open(self.contract_source_path, 'r') as f:
            source_code = f.read()
        return source_code

    def _get_version_from_source_code(self, source_code: str):
        return source_code.split("pragma solidity")[1].split(";")[0].strip()\
                .replace('^', '').replace('=', '').replace('>', '').replace('<', '')


    def compile_sol_to_json_ast(self) -> dict:
        print("downloading compiler, version: ", self.version)
        solcx.install_solc(self.version)
        solcx.set_solc_version(self.version)
        return solcx.compile_source(self._source_code, output_values=['ast'], solc_version=self.version)

    def save_solc_ast_json(self, name: str):
        with open(f'{SOLC_JSON_AST_FOLDER}/{name}_solc_ast.json', 'w') as f:
            json.dump(self.solc_json_ast, f, indent=4)

    def save_parsed_info_json(self, name: str):
        with open(f'{PARSED_JSON}/{name}.json', 'w') as f:
            json.dump(self.contracts_dict, f, default=lambda obj: obj.__dict__, indent=4)


    def all_contracts(self) -> List[ContractData]:
        # dict to list
        return list(self.contracts_dict.values())

    def all_contract_names(self) -> List[str]:
        return list(self.contracts_dict.keys())

    def all_abstract_contracts(self) -> List[ContractData]:
        return [contract for contract in self.all_contracts() if contract.abstract]

    def get_version(self) -> str:
        return self.version


    def base_contract_names(self) -> List[str]:
        contracts = self.all_contracts()
        base_contracts_name = []
        for contract in contracts:
            if contract.base_contracts:
                base_contracts_name += contract.base_contracts
        return list(set(base_contracts_name))

    def pruned_contracts(self) -> List[ContractData]:
        contracts = self.all_contracts()
        base_contracts_name = self.base_contract_names()
        pruned_contracts = []
        for contract in contracts:
            if contract.name not in base_contracts_name:
                pruned_contracts.append(contract)
        return pruned_contracts

    def pruned_contract_names(self) -> List[str]:
        return [c.name for c in self.pruned_contracts()]

    def contract_by_name(self, contract_name: str) -> ContractData:
        return self.contracts_dict[contract_name]

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
                                   parent_field_visibility: Optional[frozenset] = FIELD_VISIBILITY_NON_PRIVATE) -> List[Field]:
        contract = self.contract_by_name(contract_name)
        return self.fields_in_contract(contract, name_only, field_visibility, parent_field_visibility)

    def functions_in_contract(self, contract: ContractData,
                              name_only: bool = False,
                              function_visibility: Optional[frozenset] = None,
                              check_base_contract=True) -> List[Function]:
        functions = contract.functions
        base_contract = []
        if check_base_contract:
            base_contract = contract.base_contracts

        for base_contract_name in base_contract:
            function_list = self.functions_in_contract_by_name(base_contract_name)
            functions.extend(function_list)

        if (function_visibility is not None) and (function_visibility != self.FUNC_VISIBILITY_ALL):
            functions = [n for n in functions if n.visibility in function_visibility]

        if name_only:
            return [n.name for n in functions]
        return functions


    def functions_in_contract_by_name(self, contract_name: str, name_only: bool = False, ) -> List[Function | str]:
        fns = self.contract_by_name(contract_name).functions
        if name_only:
            return [fn.name for fn in fns]
        return fns

    def abstract_function_in_contract_by_name(self, contract_name: str, name_only: bool = False) -> List[Function | str]:
        # return all abstract functions for a given "contract name"
        fns = [fn for fn in self.functions_in_contract_by_name(contract_name) if fn.abstract]
        if name_only:
            return [fn.name for fn in fns]
        return fns

    def function_by_name(self, contract_name: str, function_name: str) -> Function:
        contract = self.contract_by_name(contract_name)
        funcs    = self.functions_in_contract(contract)
        return next(fn for fn in funcs if fn.name == function_name)


    def get_all_literals(self) -> List[str]:
        pass # TODO

    def get_all_addresses(self) -> List[str]:
        pass # TODO

    def get_fallback_functions(self, contract_name: str) -> List[str]:
        return self.functions_in_contract_by_name(contract_name, name_only=True)

if __name__ == '__main__':
    ast = SolidityAST(f'./contracts/inheritance_contracts.sol')
    ast.save_parsed_info_json('inheritance_contracts')
    # self.assertEqual('0.7.2', ast.get_version(), 'Version should be 0.7.2')
    print(ast.get_version())