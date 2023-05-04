import copy
from operator import itemgetter
from semantic_version import Version
import addict
import solcx
import os
from typing import Collection, Dict, Optional, List, Any, Union
from functools import cached_property, cache

from .fields import Field, Function, ContractData, Modifier, Event, Literal
from .version_cfg import v_keys
from . import ast_shared as s
from .base_parser import BaseParser, SolidityAstError


class CombinedJsonParser(BaseParser):
    def __init__(self, contract_source_path: str, version=None, retry_num=None, solc_options={}, lazy=False, solc_outputs=None, try_install_solc=False):
        self.file_path = None
        self.root_path = None
        self.is_standard_json = False

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

        self.original_compilation_output :Optional[Dict] = None
        self.try_install_solc = try_install_solc
        self.solc_outputs = solc_outputs
        self.solc_options = solc_options
        self.import_remappings = solc_options.get('import_remappings')
        base_path = solc_options.get('base_path')
        self.base_path = os.path.abspath(base_path) if base_path else None
        self.allow_paths = solc_options.get('allow_paths')
        self.retry_num = retry_num or 0
        self.allowed_solc_versions = self.source and s.get_solc_candidates(self.source) or s.get_all_installable_versions()
        self.solc_candidates = list(self.allowed_solc_versions)
        self.exact_version: str   = version or self.solc_candidates[-1] or consts.DEFAULT_SOLC_VERSION

        self.version_key: str     = self._get_version_key()
        self.keys: addict.Dict    = v_keys[self.version_key]
        self.prepare_by_version()

        if not lazy:
            self.build()

    def build(self):
        self.compile()
        self.contracts_dict: Dict = self._parse()

    @cached_property
    def exported_symbols(self) -> Dict[str, int]:
        if self.v8:
            return s.symbols_to_ids_from_ast_v8(self.solc_json_ast)
        else:
            return s.symbols_to_ids_from_ast_v7(self.solc_json_ast)


    @cached_property
    def raw_version(self):
        return s.version_str_from_source(self.source)


    def compile(self):
        current_working_dir = os.getcwd()
        try:
            if self.try_install_solc:
                solcx.install_solc(self.exact_version)
            solcx.set_solc_version(self.exact_version)
            if self.root_path:
                os.chdir(self.root_path)
                self.root_path = os.getcwd()

            compiler_options = dict(self.solc_options)
            overwritten_options = dict(base_path=self.base_path,
                                       import_remappings=self.import_remappings,
                                       output_values=self.solc_outputs or self.solc_compile_outputs,
                                       solc_version=self.exact_version)
            compiler_options.update(overwritten_options)
            if self.compile_type == "file":
                out = solcx.compile_files(self.file_path, **compiler_options)
            else:
                out = solcx.compile_source(self.source, **compiler_options)
            self.original_compilation_output = out
            self.solc_json_ast = {k.split(':')[-1]: v for k, v in out.items()}
        except Exception as e:
            if self.retry_num > 0:
                self.retry_num -= 1
                # self.exact_version = s.get_increased_version(self.exact_version, install=self.try_install_solc)
                self.exact_version, self.solc_candidates = s.find_next_version_in_candidates(self.exact_version, self.solc_candidates)
                self.prepare_by_version()
                self.compile()
            else:
                raise SolidityAstError(f"Compile failed with solc version {self.exact_version}, err msg: {e}")
        finally:
            os.chdir(current_working_dir)



    @cache
    def __parse_asm_data(self, contract_name, deploy=False) -> Dict[str, Any]:
        '''Parse `asm.data` returns a dict of
        - `idx` source file index, default to 0
        - `code` list,
        - `pc2idx` a dict from program counter to `code` index'''

        combined_json = self.solc_json_ast
        contract = combined_json.get(contract_name)
        if contract is None:
            raise SolidityAstError(f'Contract {contract_name} not found in compiled json')
        asm_data = contract.get('asm').get('.code') if deploy else contract.get('asm').get('.data')
        # deploys = contract.get('asm').get('.code')
        opcodes = contract.get('opcodes').split()

        # contract.get('asm').get('sourceList') is introduced in 0.8.15, it is not put in get_source_list() for 2 reasons
        # 1. it is quite a new feature, get_source_list() is to support more common cases.
        # 2. contract.get('asm').get('sourceList') requires you to know the contract name first, get_source_list() is
        #    independent of contract names.
        source_list = contract.get('asm').get('sourceList') if contract.get('asm').get('sourceList') else self.get_source_list()

        if not deploy:
            opcodes = s.skip_deploys(opcodes)

        if not (opcodes or asm_data):
            raise(SolidityAstError('Missing required params!'))

        if deploy:
            code = asm_data
        else:
            code = asm_data.get(f'{0}').get('.code')

        offset = 0  # address offset / program counter
        idx = 0     # index of code list
        idx2pc = {} # dict: index -> pc
        op_idx = 0  # idx value in contract opcodes list

        i = 0
        seen_targets = set()
        while i < len(code):
            c = code[i]
            i += 1
            idx2pc[idx] = offset
            size = 2  # opcode size: one byte as hex takes two chars
            datasize = 0

            # print(f'{contract_name} pc {offset} c {c}')

            opcode = c.get('name').split()[0]

            s.record_jumps(opcode, code, i-1, offset, seen_targets)

            if opcode == 'PUSHDEPLOYADDRESS':
                i += 2
                continue

            if (not opcode.isupper()):
                idx += 1
                continue
            if opcode.startswith('PUSH'):
                op = opcodes[op_idx]
                try:
                    datasize = int(op[4:]) * 2
                except:
                    continue
                op_idx += 1

            size += datasize
            # print(f'PC {offset:4} IDX: {idx:4} {c}')
            idx += 1
            offset += int(size / 2)
            op_idx += 1

        pc2idx = {v: k for k, v in idx2pc.items()}
        return dict(code=code, pc2idx=pc2idx, source_list=source_list, seen_targets=seen_targets)

    @cache
    def get_source_list(self):
        """
        explanation on `yul_support_flag`:
        contract.get('asm').get('sourceList') is introduced very lately in 0.8.15. In this sourceList we get from the
        output, "#utility.yul" is at last. For example, if there are two files, a.sol and b.sol, the sourceList will
        look like: ["a.sol", "b.sol", "#utility.yul"]. But in the earlier version, we get the sourceList by analyzing
        the AST. Yul is introduced in solidity in 0.7.2. So between 0.7.2 and 0.8.15, we want to get a same output
        from self.get_source_list(). So we check if there are generated-sources and generated-sources-runtime in it
        by using the yul_support_flag then we append "#utility.yul" to the list accordingly.
        """
        source_list = []
        idx2path = {}
        yul_support_flag = False
        for contract_name in self.solc_json_ast.keys():
            absolute_path = self.source_path_by_contract(contract_name)
            idx = s.get_in(self.solc_json_ast, contract_name, 'ast', 'src').split(':')[-1]
            idx2path[int(idx)] = absolute_path
            if self.solc_json_ast.get(contract_name).get('generated-sources') and \
                    self.solc_json_ast.get(contract_name).get('generated-sources-runtime'):
                yul_support_flag = True
        sort_keys = sorted(idx2path.keys())
        for idx in sort_keys:
            source_list.append(idx2path[idx])

        if yul_support_flag:
            source_list.append("#utility.yul")
        return source_list

    def get_line_number_range_and_source(self, line_number_range_raw: list):
        start_index, offset, source_file_idx = line_number_range_raw
        source_list = self.get_source_list()
        source_path = self.__source_path_from_source_list(source_list, source_file_idx)
        source_code_bytes = self.__source_code_from_source_path(source_path).encode()
        start_line = source_code_bytes[:start_index].decode().count('\n') + 1
        end_line = start_line + source_code_bytes[start_index:start_index + offset].decode().count('\n')
        return (start_line, end_line), source_code_bytes.decode()

    def source_path_by_contract(self, contract_name) -> Optional[str]:
        path = None
        if self.v8:
            path = s.get_in(self.solc_json_ast, contract_name, 'ast', 'absolutePath')
        else:
            path = s.get_in(self.solc_json_ast, contract_name, 'ast', 'attributes', 'absolutePath')

        base_path = self.base_path or self.root_path
        return None if (not path) or path == '<stdin>' else os.path.join(base_path, path)

    def source_by_lines(self, contract_name: str, line_start: int, line_end: int) -> str:
        '''Get source code by contract name and line numbers, line numbers are zero indexed'''
        source_path = self.source_path_by_contract(contract_name)
        if source_path:
            with open(source_path, 'r') as f:
                source = f.read()
        else:
            source = self.source

        return source.split('\n')[line_start: line_end]

    @cache
    def all_pcs(self, contract_name: str, deploy: bool) -> set[int]:
        '''Return all program counters by contract name'''
        asm = self.__parse_asm_data(contract_name, deploy=deploy)
        return set((s.get_in(asm, 'pc2idx') or {}).keys())

    @cache
    def all_jumps(self, contract_name: str, deploy) -> set[int]:
        '''Return all JUMP, JUMPI destinations by contract name'''
        asm = self.__parse_asm_data(contract_name, deploy=deploy)
        return asm['seen_targets']

    def coverage(self, contract_name: str, pcs: Collection[int]) -> float:
        all_pcs = self.all_pcs(contract_name)
        return len(set(pcs)) / len(all_pcs) * 100 if all_pcs else 0

    def __source_path_from_source_list(self, source_list: Optional[List[str]], source_index: Optional[int]) -> Optional[str]:
        if source_index is not None and source_list:
            return source_list[source_index]
        return None

    def __source_code_from_source_path(self, source_path):
        base_path = self.base_path or self.root_path
        if base_path and source_path and source_path != '<stdin>':
            source_path = os.path.join(base_path, source_path)
            with open(source_path, 'r') as f:
                source_code = f.read()
        else:
            source_code = self.source
        return source_code


    def source_by_pc(self, contract_name: str, pc: int, deploy=False) -> Dict[str, Any]:
        """
        Get source code by program counter:
        - `pc`: program counter
        - `deploy`: set to true to search in deploy opcodes
        """
        code, pc2idx, source_list = itemgetter('code', 'pc2idx', 'source_list')(self.__parse_asm_data(contract_name, deploy=deploy))
        pc_idx = pc2idx.get(pc)
        part = code[pc_idx]
        if part.get('source') is not None:
            source_idx = part['source']
        else:
            src_mapping = self.solc_json_ast[contract_name]['srcmap-runtime']
            parsed_mapping = s.parse_src_mapping(src_mapping)
            mapping_idx = list(pc2idx.values()).index(pc_idx)
            source_idx = parsed_mapping[mapping_idx].get('f')

        begin, end = itemgetter('begin', 'end')(part)
        source_idx = source_idx if source_idx is not None else list(self.solc_json_ast.keys()).index(contract_name)
        source_path = self.__source_path_from_source_list(source_list, source_idx)

        # NOTE: assuming yul file is at the last in the generated source list
        # e.g. [a.sol, util/b.sol, #utility.yul]
        has_yul = len(source_list) > 1
        yul_index = len(source_list) - 1 if has_yul else -1

        if source_idx == yul_index and self.v8 and not deploy:
            combined_source = self.solc_json_ast[contract_name]['generated-sources-runtime'][0]['contents']
        elif source_idx == yul_index and self.v8 and deploy:
            combined_source = self.solc_json_ast[contract_name]['generated-sources'][0]['contents']
        else:
            combined_source = self.__source_code_from_source_path(source_path)
        # assumes utf8 encoding here
        source_as_bytes = combined_source.encode()
        fragment = source_as_bytes[begin:end].decode()
        # print ("fragment ", fragment)
        linenums = (source_as_bytes[:begin].decode().count('\n') + 1,
                    source_as_bytes[:end].decode().count('\n') + 1)
        return dict(pc=pc, fragment=fragment, begin=begin, end=end, linenums=linenums, source_idx=source_idx, source_path=(source_path or self.file_path))

    def get_any(self, *keys) -> Any:
        '''Get any value by keys from the original compiled ast data'''
        return s.get_in(self.original_compilation_output, *keys)

    def get_deploy_bin_by_contract_name(self, contract_name: str) -> Optional[str]:
        return s.get_in(self.solc_json_ast, contract_name, 'bin')

    def qualified_name_from_hash(self, hsh: str)->str:
        '''Get fully qualified contract name from 34 character hash'''
        return next(full_name for full_name in self.original_compilation_output.keys() if s.keccak256(full_name)[:34] == hsh)

    def get_deploy_bin_by_hash(self, hsh: str) -> Optional[str]:
        '''Get deployment binary by hash of fully qualified contract / library name'''
        return self.get_any(self.qualified_name_from_hash(hsh), 'bin')

    def get_literals(self, contract_name: str, only_value=False) -> dict:
        """
        Get all literals(number, address, string, other) in the contract.
        for 'other' type, if only_value is True, return the string value
        - `contract_name`: contract_name in string
        - `only_value`: set to true to get only values, otherwise get all literal objects
        """

        literals_nodes = set() # save data here
        root_node = self.solc_json_ast[contract_name]['ast']
        contract_node = None
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
