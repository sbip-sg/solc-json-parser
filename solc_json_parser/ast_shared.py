import copy
from operator import itemgetter
from semantic_version import Version
import semantic_version
import logging
import addict
import warnings
import solcx
import json
import os
import re
from typing import Dict, Optional, List, Any, Tuple, Union
from functools import reduce, wraps
from Crypto.Hash import keccak

SOLC_JSON_AST_FOLDER = "./solc_json_ast"
PARSED_JSON = "./parsed_json"

INSTALLABLE_VERSION = []

INTERFACE_OR_LIB_KIND = set(['interface', 'library'])

DEPLOY_START_OPCODES = [
    # For solidity 0.4.23 and above
    [
        "PUSH1",
        "0x80",
        "PUSH1",
        "0x40",
        "MSTORE",
    ],
    # For lower solidity version
    [
        "PUSH1",
        "0x60",
        "PUSH1",
        "0x40",
        "MSTORE",
    ],
]

def keccak256(s: str) -> str:
    k = keccak.new(digest_bits=256)
    k.update(s.encode())
    return k.hexdigest()

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

def assoc_in(d, keys, value):
    """Associates a value with a sequence of keys in a nested dictionary"""
    key = keys[0]
    if len(keys) == 1:
        d[key] = value
    else:
        if key not in d or not isinstance(d[key], dict):
            d[key] = {}
        assoc_in(d[key], keys[1:], value)
    return d


def get_all_installable_versions():
    '''
    Returns a cached list of solc versions available for install,
    version list is sorted in ascending order
    '''
    global INSTALLABLE_VERSION
    if INSTALLABLE_VERSION:
        return INSTALLABLE_VERSION
    else:
        INSTALLABLE_VERSION = sorted(solcx.get_installable_solc_versions())
        return INSTALLABLE_VERSION

def version_str_from_line(line) -> Optional[str]:
    '''
    Extract solc version string from input line
    '''
    if line.strip().startswith('pragma') and 'solidity' in line:
        ver = line.strip().split(maxsplit=2)[-1].split(';', maxsplit=1)[0]
        if 'solidity' in ver:
            ver = ver.split('solidity', maxsplit=1)[-1]
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

def get_solc_candidates(source_or_source_file: str) -> List[str]:
    merged_version = version_str_from_source(source_or_source_file)

    if not merged_version:
        return []

    spec = semantic_version.NpmSpec(merged_version)
    return [str(v) for v in spec.filter(get_all_installable_versions())]

def detect_solc_version(source_or_source_file: str) -> Optional[str]:
    '''
    Detect solc version from a flatten source. Input can be a single file or source code string
    '''
    versions = get_solc_candidates(source_or_source_file)
    return versions[-1] if versions else None


def symbols_to_ids_from_ast_v8(ast: dict) -> Dict[str, int]:
    syms = [c['ast']['exportedSymbols'] for c in ast.values()]
    return {k: v[0] for m in syms for k, v in m.items()}


def symbols_to_ids_from_ast_v7(ast: Dict[Any, Any]) -> Dict[str, int]:
    syms = [c['ast']['attributes']['exportedSymbols'] for c in ast.values()]
    return {k: v[0] for m in syms for k, v in m.items()}


def find_next_version_in_candidates(current_version: str, solc_candidates: List[str]) -> Tuple[str, List[str]]:
    """Try to get the next version"""
    ver = Version(current_version)
    try_next_version = Version(major=ver.major, minor= ver.minor - 1, patch=0)
    print(f'try_next_version: {try_next_version} solc_candidates: {solc_candidates}')
    version = None
    # print(f'try_next_version: {try_next_version} solc_candidates: {solc_candidates}')
    if str(try_next_version) in solc_candidates:
        version = str(try_next_version)
        solc_candidates = [v for v in solc_candidates if Version(v) < try_next_version]

    elif solc_candidates:
        version = str(solc_candidates[-1])
        solc_candidates = solc_candidates[:-1]
    if not version:
        raise ValueError(f'No next solc version available for {current_version}')
    return version, solc_candidates

def skip_deploys(opcodes, deploy_sig_idx=0):
    if deploy_sig_idx >= len(DEPLOY_START_OPCODES):
        raise SolidityAstError(f'Code deploy sequence not found in opcodes: {opcodes}')
    offset = 1
    match_idx = 0
    deploy_start_sequence = DEPLOY_START_OPCODES[deploy_sig_idx]

    while offset < len(opcodes):
        if opcodes[offset] == deploy_start_sequence[match_idx]:
            match_idx += 1
            if match_idx == len(deploy_start_sequence):
                break
        else:
            match_idx = 0
        offset += 1

    if offset < len(opcodes):
        return opcodes[offset - len(deploy_start_sequence) + 1:]
    return skip_deploys(opcodes, deploy_sig_idx+1)


def parse_src_mapping(srcmap: str):
    def _reduce_fn(accumulator, current_value):
        last, *tlist = accumulator
        return [
            {
                's': int(current_value['s'] or last['s']),
                'l': int(current_value['l'] or last['l']),
                'f': int(current_value['f'] or last['f']),
            },
            last,
            *tlist
        ]

    parsed = srcmap.split(";")
    parsed = [l.split(':') for l in parsed]
    t = []
    for l in parsed:
        if len(l) >= 3:
            t.append(l[:3])
        else:
            t.append(l + [None] * (3 - len(l)))
    parsed = [{'s': s if s != "" else None, 'l': l, 'f': f} for s, l, f in t]
    parsed = reduce(_reduce_fn, parsed, [{}])
    parsed = list(reversed(parsed[:-1]))
    return parsed


def process_literal_node(literals_nodes, only_value):
    def _process_other_literal_node(literal_node, literals, only_value):
        try:
            if only_value:
                literals['other'].add(literal_node.str_value)
            else:
                literals['other'].add(literal_node)
        except AttributeError:
            pass

    literals = dict(number=set(), string=set(), address=set(), other=set())
    for literal in literals_nodes:
        try:
            if literal.sub_type is None and literal.token_type == 'number':
                if only_value and literal.str_value.isdecimal():
                    literals['number'].add(int(literal.str_value))
                else:
                    literals['number'].add(literal)
            elif literal.sub_type.startswith("address"):
                if only_value:
                    literals['address'].add(literal.str_value)
                else:
                    literals['address'].add(literal)
            elif literal.sub_type.startswith("int"):
                if only_value:
                    if literal.str_value.startswith('0x'):
                        literals['number'].add(int(literal.str_value, 16))
                    elif literal.sub_type.split()[1].isdecimal():
                        literals['number'].add(int(literal.sub_type.split()[1]))
                    else:
                        literals['number'].add(int(literal.str_value))
                else:
                    literals['number'].add(literal)
            # check if string in token_type, ignore case
            elif literal.sub_type.startswith("literal_string"):
                if only_value:
                    literals['string'].add(literal.str_value)
                else:
                    literals['string'].add(literal)
            elif literal.sub_type.startswith("bool"):
                continue
            else:
                _process_other_literal_node(literal, literals, only_value)
        except Exception as e:
            _process_other_literal_node(literal, literals, only_value)

    return literals


def record_jumps(opcode: str, code: list[Dict[str, Any]], idx: int, pc: int, seen_targets: set[int]) -> set[int]:
    if opcode == 'JUMPI':
        seen_targets.add(int(code[idx-1].get('value')))
        seen_targets.add(int(pc + 1))

    return seen_targets

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


class SolidityAstError(ValueError):
    pass


def deprecated_class(cls):
    @wraps(cls, updated=())
    class DeprecatedClass(cls):
        def __init__(self, *args, **kwargs):
            warnings.warn(
                f"The {cls.__name__} class is deprecated and will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )
            super().__init__(*args, **kwargs)

    return DeprecatedClass
