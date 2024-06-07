import subprocess
import json
import os
from typing import Tuple, Callable, List, Union, Optional, Dict
from functools import cached_property, cache
from .version_cfg import v_keys
from . import ast_shared as s
from .ast_shared import SolidityAstError, solc_bin
from .base_parser import BaseParser
from .fields import Function
import sys

def node_contains(src_str: str, pc_source: dict) -> bool:
    """
    Check if the source code contains the given pc_source
    """
    if not src_str:
        return False
    offset, length, _fidx = list(map(int, src_str.split(':')))
    return offset <= pc_source['begin'] and offset + length >= pc_source['end']

def compile_standard(version: str, input_json: dict, solc_bin_resolver: Callable[[str], str] = solc_bin, cwd: Optional[str]=None):
    '''
    Compile standard input json and parse output as json.
    Parameters:
        version: solc version. Example: 0.8.13
        input_json: standard json input
        solc_bin_resolver: a function takes a solc version string and returns a full path to solc executable
    '''
    print(f'Compiling with solc version: {version}')
    solc = solc_bin_resolver(version)

    if not os.path.exists(solc):
        raise Exception(f'solc not found at: {solc}, please download all solc binaries first or provide your `solc_bin_resolver` function')


    solc_output = subprocess.check_output(
        [solc, "--standard-json",],
        input=json.dumps(input_json),
        text=True,
        stderr=subprocess.PIPE,
        cwd=cwd
    )
    return json.loads(solc_output)

def build_pc2idx(evm: dict, deploy: bool = False) -> Tuple[list, dict, dict]:
    '''
    Build pc2idx map from one evm dictionary. If deploy is True, build it using deployment code.
    Returns a tuple: (code, pc2idx, pc2opcode)
    '''
    evm_key = 'bytecode' if deploy else 'deployedBytecode'

    # opcodes list (including operand datasize information for the opcode)
    # Example path in standard json: '.contracts."FILE_PATH.SOL"."CONTRACT_NAME".evm.deployedBytecode.opcodes'
    opcodes = evm[evm_key]['opcodes'].split()
    # source code mapping blocks
    # Example path in standard json: '.contracts."FILE_PATH.SOL"."CONTRACT_NAME".evm.legacyAssembly.".data"."0".".code"'
    code = evm['legacyAssembly']['.code'] if deploy else evm['legacyAssembly']['.data']['0']['.code']

    offset = 0  # program counter: byte offset
    idx = 0     # index of source code mapping blocks
    idx2pc = {} # dict: index -> pc
    op_idx = 0  # idx value in contract opcodes list

    i = 0
    pc2opcode = {}
    while i < len(code):
        c = code[i]
        i += 1
        idx2pc[idx] = offset
        size = 2  # opcode size: one byte as hex takes two chars
        datasize = 0

        opcode = c.get('name').split()[0]
        pc2opcode[offset] = opcode


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
        # print(f'PC {offset:4} IDX: {idx:4} datasize: {datasize:2} {c}')
        idx += 1
        offset += int(size / 2)
        op_idx += 1

    pc2idx = {v: k for k, v in idx2pc.items()}
    return code, pc2idx, pc2opcode

def source_content_by_file_key(input_json: dict, filename: str):
    '''
    Get source code content by unique filename
    '''
    return s.get_in(input_json, 'sources', filename, 'content')

def filename_by_fid(output_json: dict, fid: int) -> str:

    for k, source in output_json['sources'].items():
        if fid == source['id']:
            filename = k
            break

    return filename

def source_content_by_fid(input_json: dict, output_json: dict, fid: int):
    filename = filename_by_fid(output_json, fid)
    return source_content_by_file_key(input_json, filename)

def source_by_pc(code, pc2idx, input_json: dict, output_json: dict, pc: int, resolve_yul_block: Optional[Callable]=None):
    # code, pc2idx, *_ = build_pc2idx(evm, deploy)
    code_len = len(code)

    block = None
    for k in range(pc, -1, -1):
        idx = pc2idx.get(k, None)
        if idx is not None:
            if idx >= code_len: # code index is outside code list
                continue
            block = code[idx]
            break

    if block is None:
        return None

    fid = block.get('source', 0) # some times there is no `source` field.
    begin = block.get('begin')
    end = block.get('end')
    # name = block.get('name')

    file_key = None
    for k, source in output_json['sources'].items():
        if fid == source['id']:
            file_key = k
            break

    if not file_key and resolve_yul_block is not None:
        r = resolve_yul_block(block)
        if r:
            r['pc'] = pc
            return r
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


def override_settings(input_json):
    """
    Override settings:
    - Disable optimization which could confuse source mapping
    - Mark all fields to be generated in the outputs for analysis
    """
    s.assoc_in(input_json, ['settings', 'optimizer', 'enabled'], False)
    s.assoc_in(input_json, ['settings', 'outputSelection'], {'*': {'*': [ '*' ], '': ['ast']}})
    input_json['language']= input_json.get('language', 'Solidity')
    return input_json


class StandardJsonParser(BaseParser):
    def __init__(self, input_json: Union[dict, str], version: str, solc_bin_resolver: Callable[[str], str] = solc_bin, cwd: Optional[str] = None,
                 retry_num: Optional[int]=0,
                 try_install_solc: Optional[bool]=False,
                 solc_options: Optional[Dict] = {}):
        if retry_num is not None and retry_num > 0:
            raise Exception('StandardJsonParser does not support retry')

        if try_install_solc:
            print('StandardJsonParser does not support try_install_solc, option will be ignored', file=sys.stderr)

        if solc_options:
            print('StandardJsonParser does not support solc_options, please set extra parameters to input_json instead', file=sys.stderr)

        super().__init__()
        self.file_path = None
        self.solc_version: str = version
        try:
            # try parse as json
            self.input_json: dict = input_json if isinstance(input_json, dict) else json.loads(input_json)
        except json.JSONDecodeError:
            # try use input as a plain source file
            self.input_json = StandardJsonParser.__prepare_standard_input(input_json)

        self.input_json = override_settings(self.input_json)

        self.solc_json_ast: Dict[int, dict] = {}
        self.is_standard_json = True
        self.pre_configure_compatible_fields()
        self.cwd = cwd

        self.output_json = compile_standard(version, self.input_json, solc_bin_resolver, cwd)

        if has_compilation_error(self.output_json):
            raise SolidityAstError(f"Compile failed: {self.output_json.get('errors')}" )

        self.post_configure_compatible_fields()

    @staticmethod
    def __prepare_standard_input(source: str) -> Dict:
        if '\n' not in source:
            with open(source, 'r') as f:
                source = f.read()

        input_json = {
            'language': 'Solidity',
            'sources': {
                'source.sol': {
                    'content': source
                }
            },
            'settings': {
                'optimizer': {
                    'enabled': False,
                },
                'evmVersion': 'istanbul',
                'outputSelection': {
                    '*': {
                        '*': [ '*' ],
                        '': ['ast']
                    }
                }
            }
        }
        return input_json


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
        if not content:
            return (0, 0), ""
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

    def source_by_yul_block(self, block: Dict):
        """
        Get source code by Yul block
        """
        fid = block.get('source')
        begin = block.get('begin')
        end = block.get('end')
        pred = lambda node: node and node.get('language') == 'Yul' and node.get('id') == fid
        # this does not consider deployment code or not, might be a bug
        yul_source = self.extract_node(pred, self.output_json['contracts'], first_only=True)[0]

        if not yul_source:
            return None

        source_as_bytes = yul_source['contents'].encode()
        fragment = source_as_bytes[begin:end].decode()
        linenums = (source_as_bytes[:begin].decode().count('\n') + 1,
                    source_as_bytes[:end].decode().count('\n') + 1)

        return dict(fragment=fragment, begin=begin, end=end, linenums=linenums, fid=fid, source_path=yul_source['name'])


    def source_by_pc(self, contract_name: str, pc: int, deploy=False) -> Optional[dict]:
        """
        Get source code by program counter(pc) in a contract.
        - `contract_name`: contract name in string
        - `pc`: program counter in integer
        - `deploy`: set to True if the PC is from the deployment code instead of runtime code. Default is False
        """
        evms = evms_by_contract_name(self.output_json, contract_name)
        for _, evm in evms:
            code, pc2idx, *_ = self.__build_pc2idx(evm, deploy)
            result = source_by_pc(code, pc2idx, self.input_json, self.output_json, pc, resolve_yul_block=self.source_by_yul_block)
            if result:
                return result
        return None

    def extract_node(self, pred: Callable, root_node: List[Dict], first_only=True) -> List[Dict]:
        to_visit = [root_node]
        found = []
        while True:
            if not to_visit:
                break

            node = to_visit.pop(0)

            if type(node) not in {dict, list}:
                continue

            if type(node) == list:
                to_visit += node
                continue

            children = list(node.values())

            if children:
                to_visit += children
            if pred(node):
                found.append(node)
                if first_only:
                    break

        return found

    def ast_units_by_pc(self, contract_name: str, pc: int, node_type: Optional[str], deploy=False, first_only=False) -> List[Dict]:
        """
        Get all AST units by PC
        """
        pc_source = self.source_by_pc(contract_name, pc, deploy)
        if not pc_source:
            return []
        pred = lambda node: node and (node_type is None or node.get('nodeType') == node_type) and node_contains(node.get('src'), pc_source)
        return self.extract_node(pred, self.output_json['sources'][pc_source['fid']]['ast'], first_only=first_only)

    def function_unit_by_pc(self, contract_name: str, pc: int, deploy=False) -> Optional[Dict]:
        """
        Get the function AST unit containing the PC
        """
        units = self.ast_units_by_pc(contract_name, pc, 'FunctionDefinition', deploy, first_only=True)
        return units[0] if units else None

    def ast_unit_by_pc(self, contract_name: str, pc: int, deploy=False) -> Optional[Dict]:
        """
        Get the smallest AST unit containing the PC
        """
        units = self.ast_units_by_pc(contract_name, pc, node_type=None, deploy=deploy, first_only=False)
        return units[-1] if units else None


    def all_pcs(self, contract: str, deploy: Optional[bool] = False) -> List[int]:
        """
        Returns a list of PCs inside the contract
        """
        return list(self.pc2opcode_by_contract(contract, deploy).keys())

    def __build_pc2idx(self, evm: dict, deploy: bool = False) -> Tuple[list, dict, dict]:
        """
        Returns a tuple: (code, pc2idx, pc2opcode)
        """
        return build_pc2idx(evm, deploy)

    @cache
    def pc2opcode_by_contract(self, contract_name: str, deploy: bool) -> Dict[int, str]:
        evms = evms_by_contract_name(self.output_json, contract_name)
        for _, evm in evms: # if same contract existsin in multiple files, there could be a problem
            _, _, pc2opcode = self.__build_pc2idx(evm, deploy)
            return pc2opcode
        return {}

    def function_by_name(self, contract_name: str, function_name: str) -> Function:
        """Return a function for a given contract name and function name"""
        contract = self.contract_by_name(contract_name)
        funcs    = self.functions_in_contract(contract)
        return next(fn for fn in funcs if fn.name == function_name)


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

    def source_path_by_contract(self, contract_name: str) -> str:
        """
        Get source path by contract name.
        Note:
        - May throw exception if no source file contains the contract.
        - May return unexpected result when the contract appears in multiple source files.
        """
        pred = lambda node: node and node.get('nodeType') == 'ContractDefinition' and node.get('name') == contract_name
        contract = self.extract_node(pred, self.output_json['sources'], first_only=True)[0]
        return contract['source_id']

    def all_source_path_by_contract(self, contract_name: str) -> Optional[List[str]]:
        """
        Get source path by contract name.
        """
        pred = lambda node: node and node.get('nodeType') == 'ContractDefinition' and node.get('name') == contract_name
        contracts = self.extract_node(pred, self.output_json['sources'], first_only=False)
        return [c['source_id'] for c in contracts] if contracts else []

    def source_by_lines(self, contract_name: str, line_start: int, line_end: int) -> str:
        """
        Get source code by contract name and line numbers, line numbers are zero indexed
        """
        source_path = self.source_path_by_contract(contract_name)
        content = self.input_json['sources'][source_path]['content']
        lines = content.split('\n')[line_start:line_end]
        return '\n'.join(lines)
