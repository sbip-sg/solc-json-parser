import subprocess
import json
import re
import os
from typing import Tuple, Callable, List

def solc_bin(ver: str):
    '''
    Get solc bin full path by version. By default it checks the solcx installion path.
    You can also override this function to use solc from https://github.com/ethereum/solc-bin/tree/gh-pages/linux-amd64
    '''
    return os.path.expanduser(f'~/.solcx/solc-v{ver}')

version_pattern = r'v(\d+\.\d+\.\d+)'
def simplify_version(s):
    '''
    Convert a version with sha to a simple version
    Example: v0.8.13+commit.abaa5c0e -> 0.8.13
    '''
    match = re.search(version_pattern, s or '')
    if match:
        extracted_version = match.group(1)
        return extracted_version
    else:
        return None

def compile_standard(version: str, input_json: dict, solc_bin_resolver: Callable[[str], str] = solc_bin):
    '''
    Compile standard input json and parse output as json
    '''
    solc = solc_bin_resolver(version)
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

def source_by_pc(input_json: dict, output_json: dict, pc: int, evm: dict, deploy=False):
    code, pc2idx = build_pc2idx(evm, deploy)
    code_len = len(code)
    sources_len = len(input_json['sources'])

    block = None
    for k in range(pc, -1, -1):
        idx = pc2idx.get(k, None)
        if idx is not None:
            print(idx)
            if idx >= code_len:
                continue
            t_block = code[idx]
            print(t_block)
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
    return 'Error' in errors_t



class StandardJsonParser():
    def __init__(self, input_json: dict, solc_version: str, solc_bin_resolver: Callable[[str], str] = solc_bin):
        self.input_json = input_json
        self.output_json = compile_standard(solc_version, input_json, solc_bin_resolver)
        if has_compilation_error(self.output_json):
            raise Exception('Compile failed:' + self.output_json.get('errors'))

    def source_by_pc(self, contract_name: str, pc: int, deploy=False) -> dict:
        evms = evms_by_contract_name(self.output_json, contract_name)
        for _, evm in evms:
            result = source_by_pc(self.input_json, self.output_json, pc, evm, deploy)
            if result:
                return result
