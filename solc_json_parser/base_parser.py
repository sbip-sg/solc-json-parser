import copy
from operator import itemgetter
from semantic_version import Version
import addict
import json
import solcx
import os
from typing import Collection, Dict, Optional, List, Any, Union
from functools import cached_property, cache
from .fields import Field, Function, ContractData, Modifier, Event, Literal
from .version_cfg import v_keys
from . import consts
from . import ast_shared as s


class SolidityAstError(ValueError):
    pass

class BaseParser():
    FIELD_VISIBILITY_ALL = frozenset(('default', 'internal', 'public', 'private'))
    FIELD_VISIBILITY_NON_PRIVATE = frozenset(('default', 'internal', 'public'))

    FUNC_VISIBILITY_ALL = frozenset(('external', 'private', 'internal', 'public'))
    FUNC_VISIBILITY_NON_PRIVATE = frozenset(('external', 'internal', 'public'))

    def __init__(self, contract_source_path: Optional[str], version=None, retry_num=None, standard_json: Optional[Union[dict, str]]=None, solc_options={}, lazy=False, solc_outputs=None, try_install_solc=True):
        self.file_path = None
        self.root_path = None

        if contract_source_path is not None:
            if '\n' in contract_source_path:
                self.source = contract_source_path
                self.compile_type = 'source'
            else:
                self.compile_type = 'file'
                self.file_path = os.path.abspath(contract_source_path)
                self.root_path = os.path.dirname(contract_source_path)
                with open(contract_source_path, 'r') as f:
                    self.source = f.read()
        else:
            self.compile_type = 'json'
            if not self.standard_json:
                raise SolidityAstError('Neither source code nor standard json input provided')
            self.standard_json = standard_json if type(standard_json) == dict else json.loads(standard_json)


        self.original_compilation_output :Optional[Dict] = None
        self.try_install_solc = try_install_solc
        self.solc_outputs = solc_outputs
        self.solc_options = solc_options
        self.import_remappings = solc_options.get('import_remappings')
        base_path = solc_options.get('base_path')
        self.base_path = os.path.abspath(base_path) if base_path else None
        self.allow_paths = solc_options.get('allow_paths')
        self.retry_num = retry_num or 0
        self.allowed_solc_versions = s.get_solc_candidates(self.source) or s.get_all_installable_versions()
        self.solc_candidates = list(self.allowed_solc_versions)
        self.exact_version: str   = version or self.solc_candidates[-1] or consts.DEFAULT_SOLC_VERSION
        self.exported_symbols: Dict[str, int] = {} # contract name -> id mapping, to be determined in _parse()
        self.id_to_symbols: Dict[int, str] = {} # reverse mapping of exported_symbols

        self.version_key: str     = self._get_version_key()
        self.keys: addict.Dict    = v_keys[self.version_key]
        self.prepare_by_version()

        if not lazy:
            self.build()

    def build(self):
        raise NotImplementedError

    @cached_property
    def v8(self):
        return self.version_key == "v8"

    def _get_version_key(self):
        if int(self.exact_version[2]) < 8:
            return f"v{self.exact_version[2]}"
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
                        modifiers=modifiers, line_num=line_number_range, state_mutability=state_mutability)

    def get_yul_lines(self, contract_name: str, deploy: bool) -> List[str]:
        if not self.v8:
            return []

        if deploy:
            return self.solc_json_ast.get(contract_name).get('generated-sources')[0]['contents'].split("\n")
        else:
            return self.solc_json_ast.get(contract_name).get('generated-sources-runtime')[0]['contents'].split("\n")




    @cached_property
    def v8(self):
        return self.version_key == "v8"

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
        return Field(inherited_from=inherited_from, visibility=visibility, name=name, line_num=line_number_range)

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
        return Event(raw=raw, name=name, anonymous=anonymous, line_num=line_number_range, signature=signature)

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
        contract_id, contract_kind, is_abstract, contract_name, base_contracts, line_number_range = contract_meta_data

        functions = []
        fields = []
        modifiers = []
        events = []
        keys = self.keys
        for node in node.get(keys.children, []):
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

        return ContractData(is_abstract, contract_name, contract_kind, base_contracts, fields, functions, modifiers, line_number_range, contract_id, events)


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
