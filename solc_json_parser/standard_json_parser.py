import subprocess
import json
import os
from typing import Tuple, Callable, List, Union, Optional, Dict
from functools import cached_property
from .version_cfg import v_keys
from . import ast_shared as s
from .ast_shared import SolidityAstError, solc_bin
from .base_parser import BaseParser
from .fields import Field, Function, ContractData, Modifier, Event, Literal

def compile_standard(version: str, input_json: dict, solc_bin_resolver: Callable[[str], str] = solc_bin):
    '''
    Compile standard input json and parse output as json.
    Parameters:
        version: solc version. Example: 0.8.13
        input_json: standard json input
        solc_bin_resolver: a function takes a solc version string and returns a full path to solc executable
    '''
    solc = solc_bin_resolver(version)

    if not os.path.exists(solc):
        raise Exception(f'solc not found at: {solc}, please download all solc binaries first or provide your `solc_bin_resolver` function')

    solc_output = subprocess.check_output(
        [solc, "--standard-json",],
        input=json.dumps(input_json),
        text=True,
        stderr=subprocess.PIPE,
    )
    return json.loads(solc_output)


def build_pc2idx(evm: dict, deploy: bool = False) -> Tuple[list, dict]:
    '''
    Build pc2idx map from evm json. If deploy is True, build it for deployment code.
    Returns a tuple: (code, pc2idx)
    '''
    evm_key = 'bytecode' if deploy else 'deployedBytecode'
    opcodes = evm[evm_key]['opcodes'].split()
    code = evm['legacyAssembly']['.code'] if deploy else evm['legacyAssembly']['.data']['0']['.code']


    offset = 0  # address offset / program counter
    idx = 0     # index of code list
    idx2pc = {} # dict: index -> pc
    op_idx = 0  # idx value in contract opcodes list

    i = 0
    while i < len(code):
        c = code[i]
        i += 1
        idx2pc[idx] = offset
        size = 2  # opcode size: one byte as hex takes two chars
        datasize = 0

        opcode = c.get('name').split()[0]

        if opcode == 'PUSHDEPLOYADDRESS':
            i += 2
            continue

        if (not opcode.isupper()):
            idx += 1
            continue
        if opcode.startswith('PUSH'):
            op = opcodes[op_idx]
            try:
                datasize = int(op[4:]) * 2 if len(op) > 4 else 2
            except Exception as e:
                print(f'error: {e}')
                continue
            op_idx += 1

        size += datasize
        # print(f'PC {offset:4} IDX: {idx:4} {c}')
        idx += 1
        offset += int(size / 2)
        op_idx += 1

    pc2idx = {v: k for k, v in idx2pc.items()}
    return code, pc2idx

def source_content_by_file_key(input_json: dict, filename: str):
    '''
    Get source code content by unique filename
    '''
    return input_json['sources'][filename]['content']

def filename_by_fid(output_json: dict, fid: int) -> str:
    filename = ''
    for k, source in output_json['sources'].items():
        if fid == source['id']:
            filename = k
            break

    return filename

def source_content_by_fid(input_json: dict, output_json: dict, fid: int):
    filename = filename_by_fid(output_json, fid)
    return source_content_by_file_key(input_json, filename)

def source_by_pc(input_json: dict, output_json: dict, pc: int, evm: dict, deploy=False):
    code, pc2idx = build_pc2idx(evm, deploy)
    code_len = len(code)
    sources_len = len(input_json['sources'])

    block = None
    for k in range(pc, -1, -1):
        idx = pc2idx.get(k, None)
        if idx is not None:
            if idx >= code_len:
                continue
            t_block = code[idx]
            file_key = t_block.get('source', -1)
            if file_key >= 0 and file_key < sources_len:
                block = t_block
                break

    if block is None:
        return None

    fid = block.get('source', -1)
    begin = block.get('begin')
    end = block.get('end')
    # name = block.get('name')

    file_key = None
    for k, source in output_json['sources'].items():
        if fid == source['id']:
            file_key = k
            break

    if not file_key:
        return None

    content = source_content_by_file_key(input_json, file_key)

    highlight = content.encode()[begin:end].decode()
    line_start = content.encode()[:begin].decode().count('\n') + 1
    line_end = content.encode()[:end].decode().count('\n') + 1
    return dict(pc=pc, linenums = [line_start, line_end], fragment=highlight, fid=file_key, begin=begin, end=end, source_idx = fid, source_path = file_key)


def evms_by_contract_name(output_json: dict, contract_name: str) -> List[Tuple[str, dict]]:
    '''
    Get evm json by contract name, returns a list of dict. Each dict is a evm json.
    A list is returned because there may be multiple contracts with the same name.
    '''
    result = []
    for filename, v in output_json['contracts'].items():
        for name, c in v.items():
            if name == contract_name:
                result.append((filename, c.get('evm')))
    return result


def has_compilation_error(output_json: dict) -> bool:
    errors_t = {t.get('type') for t in output_json.get('errors', [])}
    for e in errors_t:
        if 'Error' in e:
            return True
    return False


def mark_select_all(input_json):
    """Mark all fields to be generated in the outputs for analysis"""
    input_json['settings']['outputSelection'] = {'*': {'*': [ '*' ], '': ['ast']}}
    return input_json


class StandardJsonParser(BaseParser):
    def __init__(self, input_json: Union[dict, str], version: str, solc_bin_resolver: Callable[[str], str] = solc_bin):
        self.file_path = None
        self.solc_version: str = version
        self.input_json: dict = input_json if isinstance(input_json, dict) else json.loads(input_json)

        self.input_json = mark_select_all(self.input_json)

        self.solc_json_ast: Dict[int, dict] = {}
        self.is_standard_json = True
        self.pre_configure_compatible_fields()


        self.output_json = compile_standard(version, self.input_json, solc_bin_resolver)
        if has_compilation_error(self.output_json):
            raise SolidityAstError(f"Compile failed: {self.output_json.get('errors')}" )

        self.post_configure_compatible_fields()


    def prepare_by_version(self):
        super().prepare_by_version()
        # NOTE the whole v_keys seems unneccessary when using standard json input, all format follows v8 version of combined json outputs
        self.keys = v_keys['v8']


    def pre_configure_compatible_fields(self):
        """
        Configure the fields to maintain backward compatibility with the CombinedJsonParser, called before compilation
        """
        self.raw_version = self.solc_version
        self.exact_version = self.solc_version
        self.prepare_by_version()

    def __build_ast(self):
        ast_dict = {}
        for filename, source in self.output_json.get('sources').items():
            # key = source['id']
            ast_dict.update({filename: source})
        return ast_dict


    def get_line_number_range_and_source(self, slf):
        start, length, fid = slf
        content = source_content_by_fid(self.input_json, self.output_json, fid)
        source_code_bytes = content.encode()
        start_line = source_code_bytes[:start].decode().count('\n') + 1
        end_line = start_line + source_code_bytes[start:start + length].decode().count('\n')
        return (start_line, end_line), source_code_bytes.decode()


    def _get_contract_meta_data(self, node: Dict) -> tuple:
        # line number range is the same for all versions
        line_number_range_raw = list(map(int, node.get('src').split(':')))
        line_number_range, _ = self.get_line_number_range_and_source(line_number_range_raw)
        contract_id = node.get('id')

        # assert node.get('name') is not None
        # assert node.get('abstract') is not None
        # assert node.get('baseContracts') is not None

        contract_kind = node.get('contractKind')

        is_abstract = node.get('abstract')

        if node.get('baseContracts') is not None:
            base_contracts = self._get_base_contracts(node.get('baseContracts'))
        else:
            base_contracts = node.get('contractDependencies')
        contract_name = node.get('name')

        return contract_id, contract_kind, is_abstract, contract_name, base_contracts, line_number_range


    @cached_property
    def exported_symbols(self) -> Dict[str, int]:
        return s.symbols_to_ids_from_ast_v8(self.solc_json_ast)


    def post_configure_compatible_fields(self):
        """
        Configure the fields to maintain backward compatibility with the CombinedJsonParser, called after compilation
        """
        self.solc_json_ast = self.__build_ast()
        self.contracts_dict = self._parse()


    def source_by_pc(self, contract_name: str, pc: int, deploy=False) -> Optional[dict]:
        evms = evms_by_contract_name(self.output_json, contract_name)
        for _, evm in evms:
            result = source_by_pc(self.input_json, self.output_json, pc, evm, deploy)
            if result:
                return result
        return None


    def __get_binary(self, contract_name: str, filename: Optional[str], deploy=False) -> List[Tuple[str, str, str]]:
        """
        Returns a list of tuples, each tuple is: `(filename, contract_name, binary)`
        """
        bins = []
        evms = evms_by_contract_name(self.output_json, contract_name)
        bytecode_key = 'bytecode' if deploy else 'deployedBytecode'
        for _filename, evm in evms:
            bin = evm.get(bytecode_key, {}).get('object')
            if bin and ((not filename) or _filename == filename):
                bins.append((filename, contract_name, bin))
        return bins

    def get_runtime_binary(self, contract_name: str) -> List[Tuple[str, str, str]]:
        """
        Returns a list of tuples, each tuple is: `(filename, contract_name, binary)`
        """
        return self.__get_binary(contract_name, None, deploy=False)

    def get_deployment_binary(self, contract_name: str) -> List[Tuple[str, str, str]]:
        """
        Returns a list of tuples, each tuple is: `(filename, contract_name, binary)`
        """
        return self.__get_binary(contract_name, None, deploy=True)

    def qualified_name_from_hash(self, hsh: str)->Optional[Tuple[str, str]]:
        '''Get fully qualified contract name from 34 character hash'''
        for filename, m_contract in self.output_json.get('contracts').items():
            for contract_name, contract in m_contract.items():
                full_name = f'{filename}:{contract_name}'
                if hsh == s.keccak256(full_name)[:34]:
                    return (filename, contract_name)

        return None

    # TODO test
    def get_deploy_bin_by_hash(self, hsh: str) -> Optional[str]:
        '''Get deployment binary by hash of fully qualified contract / library name'''
        r = self.qualified_name_from_hash(hsh)
        if not r:
            return None
        filename, contract_name = r
        return self.__get_binary(contract_name, filename, deploy=True)[0][2]


    def get_literals(self, contract_name: str, only_value=False) -> dict:
        """
        Get all literals(number, address, string, other) in the contract.
        for 'other' type, if only_value is True, return the string value
        - `contract_name`: contract_name in string
        - `only_value`: set to true to get only values, otherwise get all literal objects
        """

        literals_nodes = set()
        contract_node = None
        for filename, unit in self.solc_json_ast.items():
            root_node = unit.get('ast')
            for i, node in enumerate(root_node[self.keys.children]):
                if node[self.keys.name] == "ContractDefinition":
                    info_node = node if self.v8 else node.get('attributes')
                    if info_node['name'] == contract_name:
                        contract_node = node
                        break

        # traverse the dictionary and get all the literals recursively
        self._traverse_nodes(contract_node, literals_nodes)

        literals = s.process_literal_node(literals_nodes, only_value)

        return literals
