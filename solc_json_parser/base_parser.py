from semantic_version import Version
from typing import Dict, Optional, List, Union, Any
from functools import cached_property, cache
from .fields import Field, Function, ContractData, Modifier, Event, Literal
from .version_cfg import v_keys
from . import ast_shared as s
from .ast_shared import SolidityAstError
import copy

def add_inherited_function_fields(data_dict: Dict[int, ContractData]):
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


class BaseParser():
    FIELD_VISIBILITY_ALL = frozenset(('default', 'internal', 'public', 'private'))
    FIELD_VISIBILITY_NON_PRIVATE = frozenset(('default', 'internal', 'public'))

    FUNC_VISIBILITY_ALL = frozenset(('external', 'private', 'internal', 'public'))
    FUNC_VISIBILITY_NON_PRIVATE = frozenset(('external', 'internal', 'public'))

    def __init__(self) -> None:
        # To be overwritten by child classes
        self.exact_version: str = ""
        self.id_to_symbols: Dict[int, str] = {} # mapping from a unique id to symbol string
        self.contracts_dict: dict = {}
        self.exported_symbols: Dict[str, int] = {}
        self.keys = None
        self.is_standard_json = False
        self.file_path = None # to be overridden by CombinedJsonParser
        self.pc2opcode = {}

    def build(self):
        raise NotImplementedError

    @cached_property
    def v8(self):
        return self.version_key == "v8" or self.is_standard_json

    def _get_version_key(self):
        minor = Version(self.exact_version).minor
        if minor < 8:
            return f"v{minor}"
        else:
            return "v8"

    def prepare_by_version(self):
        """Prepare compilation outputs, etc by the current `exact_version`"""
        ver = Version(self.exact_version)
        outputs = ['abi', 'bin', 'bin-runtime', 'srcmap', 'srcmap-runtime', 'asm', 'opcodes', 'ast']

        self.version_key: str     = self._get_version_key()
        self.keys: addict.Dict    = v_keys[self.version_key]
        # clear cache
        try: del self.v8
        except AttributeError: pass

        if ver >= Version("0.6.5"):
            outputs.append('storage-layout')

        if self.v8:
            outputs += ['generated-sources-runtime', 'generated-sources', ]

        self.solc_compile_outputs = outputs

    def _get_base_contracts(self, data: List[Dict]) -> List:
        base_contracts = []
        for base_contract in data:
            if base_contract is None: # this is to handle [null] in json
                continue
            base_contracts.append(base_contract['baseName']['referencedDeclaration'])
        return base_contracts

    def get_raw_from_src(self, node):
        line_number_range_raw = list(map(int, node.get('src').split(':')))
        start, offset, source_file_idx = line_number_range_raw
        line_number_range, source = self.get_line_number_range_and_source(line_number_range_raw)
        raw = source.encode()[start: start+offset].decode()
        return raw, line_number_range

    def get_signature(self, function_name, parameters, kind='function') -> str:
        if kind in ['constructor']:
            return ''

        signature = "" + function_name + "("
        param_type_str = ""
        if self.v8:
            for param in parameters['parameters']:
                param_type_str += param['typeDescriptions']['typeString'] + ", "
        else:  # v4, v5, v6, v7
            for param in parameters['children']:
                param_type_str += param['attributes']['type'] + ", "

        param_type_str = param_type_str[:-2]  # remove the last ", "
        signature += param_type_str + ")"
        return signature

    def _process_function(self, node: Dict) -> Function:
        def _get_modifiers(node: Dict) -> List[str]:
            modifiers = []
            if self.v8:
                for modifier in node['modifiers']:
                    modifiers.append(modifier['modifierName']['name'])
                return modifiers
            else:
                # if None in node['modifiers']:
                #     return []
                # else:
                # if no modifiers, will return []
                for child in node['modifiers']:
                    if s.get_in(child, 'children', 0, 'attributes', 'type') == "modifier ()":
                        modifiers.append(child['children'][0]['attributes']['value'])
            return modifiers

        # line number range is the same for all versions
        raw, line_number_range = self.get_raw_from_src(node)
        if self.v8:
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
        kind = node.get('kind')
        state_mutability = node.get('stateMutability')

        signature = self.get_signature(name, parameters, kind)
        return_signature = self.get_signature("", return_type, kind)
        return Function(inherited_from=inherited_from, abstract=abstract, visibility=visibility, raw=raw,
                        signature=signature, name=name, return_signature=return_signature, kind=kind,
                        modifiers=modifiers, line_num=line_number_range, state_mutability=state_mutability,
                        source_id=node.get("source_id"))

    def get_yul_lines(self, contract_name: str, deploy: bool) -> List[str]:
        if not self.v8:
            return []

        if deploy:
            return self.solc_json_ast.get(contract_name).get('generated-sources')[0]['contents'].split("\n")
        else:
            return self.solc_json_ast.get(contract_name).get('generated-sources-runtime')[0]['contents'].split("\n")




    def _process_field(self, node: Dict) -> Field:
        # line number range is the same for all versions
        line_number_range_raw = list(map(int, node.get('src').split(':')))
        line_number_range, _ = self.get_line_number_range_and_source(line_number_range_raw)

        if self.v8:
            pass
        else:  # v4, v5, v6, v7
            node = node.get("attributes")
        visibility = node.get('visibility')
        name = node.get('name')
        inherited_from = ""
        return Field(inherited_from=inherited_from, visibility=visibility, name=name, line_num=line_number_range, source_id=node.get("source_id"))

    def _process_event(self, node: Dict) -> Event:
        raw, line_number_range = self.get_raw_from_src(node)
        if self.v8:
            parameters = node.get('parameters')
        else:  # v4, v5, v6, v7
            parameters = None
            for i in range(len(node.get('children'))):
                if node.get('children')[i].get('name') == "ParameterList":
                    parameters = node.get('children')[i]
                    break
            node = node.get("attributes")

        name = node.get('name')
        anonymous = node.get('anonymous')

        signature = self.get_signature(name, parameters, "event")
        return Event(raw=raw, name=name, anonymous=anonymous, line_num=line_number_range, signature=signature, source_id=node.get("source_id"))

    def _process_modifier(self, node: Dict) -> Modifier:
        if self.v8:
            pass
        else:  # v4, v5, v6, v7
            node = node.get("attributes")
        visibility = node.get('visibility')
        name = node.get('name')
        return Modifier(visibility=visibility, name=name)

    def _get_contract_meta_data(self, node: Dict) -> tuple:
        # line number range is the same for all versions
        line_number_range_raw = list(map(int, node.get('src').split(':')))
        line_number_range, _ = self.get_line_number_range_and_source(line_number_range_raw)
        contract_id = node.get('id')

        if self.v8:
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
        source_id = node.get("source_id", "")
        contract_id, contract_kind, is_abstract, contract_name, base_contracts, line_number_range = contract_meta_data

        functions = []
        fields = []
        modifiers = []
        events = []
        keys = self.keys
        for node in node.get(keys.children, []):
            node["source_id"] = source_id
            if node[keys.name] == "FunctionDefinition":
                functions.append(self._process_function(node))
            elif node[keys.name] == "VariableDeclaration":
                fields.append(self._process_field(node))
            elif node[keys.name] == "ModifierDefinition":
                modifiers.append(self._process_modifier(node))
            elif node[keys.name] == "EventDefinition":
                events.append(self._process_event(node))
            else:
                # not implemented for other types
                pass

        return ContractData(is_abstract, contract_name, contract_kind, base_contracts, fields, functions, modifiers, source_id, line_number_range, contract_id, events)


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

    def pruned_contracts(self) -> List[ContractData]:
        contracts = self.all_contracts()
        base_contracts_name = self.base_contract_names
        pruned_contracts = [c for c in contracts \
                            if c.name not in base_contracts_name \
                            and c.kind not in s.INTERFACE_OR_LIB_KIND \
                            and not c.abstract]
        return pruned_contracts

    @cached_property
    def pruned_contract_names(self) -> List[str]:
        return [c.name for c in self.pruned_contracts()]


    def _parse(self) -> Dict:
        # todo record source file location

        data_dict = {}
        # use version key to get the correct version cfg
        keys = self.keys
        unique_file = set()

        self.id_to_symbols = {v: k for k, v in self.exported_symbols.items()}

        for ast_key in self.solc_json_ast.keys():
            source_id = ast_key.split(':')[0]
            if source_id in unique_file:
                continue

            unique_file.add(source_id)
            ast = self.solc_json_ast.get(ast_key).get('ast')
            if ast[keys.name] != "SourceUnit" or ast[keys.children] is None:
                raise SolidityAstError("Invalid AST")

            for i, node in enumerate(ast[keys.children]):
                node["source_id"] = source_id
                if node[keys.name] == "PragmaDirective":
                    continue
                elif node[keys.name] == "ContractDefinition":
                    contract = self._process_contract(node)
                    data_dict[contract.contract_id] = contract
                    assert contract.contract_id > 0, 'Missing contract_id in contract'
        add_inherited_function_fields(data_dict)
        return data_dict

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
                              check_base_contract=True) -> List[Union[Function, str]]:
        # filter and return all functions for a given contract object of type `ContractData`

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
        # return all functions for a given "contract name"(str)
        contract = self.contract_by_name(contract_name)
        return self.functions_in_contract(contract, name_only, function_visibility, check_base_contract)

    def abstract_function_in_contract_by_name(self, contract_name: str, name_only: bool = False) -> List[Any]:
        # return all abstract functions for a given "contract name"
        fns = [fn for fn in self.functions_in_contract_by_name(contract_name) if fn.abstract]
        if name_only:
            return [fn.name for fn in fns]
        return fns

    def function_by_name(self, contract_name: str, function_name: str) -> Function:
        """return a function for a given "contract name"(str) and "function name"(str)"""
        contract = self.contract_by_name(contract_name)
        funcs    = self.functions_in_contract(contract)
        return next(fn for fn in funcs if fn.name == function_name)

    def events_in_contract(self, contract: ContractData, name_only: bool = False) -> List[Union[str, Event]]:
        """return all events for a given contract object of type `ContractData`"""
        events = contract.events
        if name_only:
            return [n.name for n in events]
        return events

    def events_in_contract_by_name(self, contract_name: str, name_only: bool = False) -> List[Any]:
        """return all events for a given "contract name"(str)"""
        contract = self.contract_by_name(contract_name)
        return self.events_in_contract(contract, name_only)

    def event_by_name(self, contract_name: str, event_name: str) -> Event:
        """return an event for a given "contract name"(str) and "event name"(str)"""
        contract = self.contract_by_name(contract_name)
        events    = self.events_in_contract(contract)
        return next(ev for ev in events if ev.name == event_name)

    def all_libraries(self) -> List[ContractData]:
        return [contract for contract in self.all_contracts() if contract.kind == "library"]

    @cached_property
    def all_libraries_names(self) -> List[str]:
        return [lib.name for lib in self.all_libraries()]


    def _traverse_nodes(self, node, literals_nodes):
        if not isinstance(node, dict):
            return

        if node.get(self.keys.name) == 'Literal':
            if self.v8 and node.get('typeDescriptions'):
                literals_nodes.add(Literal(
                    hex_value=node.get('hexValue'),
                    str_value=node.get('value'),
                    sub_type=node.get('typeDescriptions').get('typeString'),
                    token_type=node.get('kind', ),
                ))
            elif not self.v8 and node.get('attributes'):
                literals_nodes.add(Literal(
                    hex_value=node.get('attributes').get('hexvalue'),
                    str_value=node.get('attributes').get('value'),
                    sub_type=node.get('attributes').get('type'),
                    token_type=node.get('attributes').get('token'),
                ))
        else:
            for k, v in node.items():
                if isinstance(v, dict):
                    self._traverse_nodes(v, literals_nodes)
                if isinstance(v, list):
                    for c in v:
                        if isinstance(c, dict):
                            self._traverse_nodes(c, literals_nodes)

    def pc2opcode_by_contract(self, contract_name: str, deploy) -> Dict[int, str]:
        # to be implemented by child classes
        ...

    @cache
    def opcode2pcs_by_contract(self, contract_name: str, deploy) -> Dict[str, set[int]]:
        pc2opcode = self.pc2opcode_by_contract(contract_name, deploy=deploy)
        out = {}
        for pc, opcode in pc2opcode.items():
            out.setdefault(opcode, set()).add(pc)

        return out
