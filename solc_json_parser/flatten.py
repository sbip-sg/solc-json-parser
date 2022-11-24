from typing import List, Tuple, Optional, Set
import os
from pathlib import Path
from os.path import abspath
from functools import cached_property


# Duplicate pragma to be dropped
F_PRGAMA_ABICODER = 'abicoder'
F_PRGAMA_ABICODERV2 = 'ABIEncoderV2'
F_PRGAMA_SMTCHECKER = 'SMTChecker'

INSTALLABLE_VERSION = []

class FlattenError(ValueError):
    pass


FlattenLine = Tuple[str, int, str]
FlattenSourceResult = List[FlattenLine]

# Replace a SPDX license line
def replace_spdx(line=None) -> Optional[str]:
    return line and line.replace('SPDX-License', 'IGNORE_LICENSE') or None

def replace_pragma(seen_meta, prag, head, tail=None) -> Optional[str]:
    if tail and head == 'pragma' and prag in tail:
        if prag in seen_meta:
            return '//{} {}\n'.format(head, head)
        seen_meta.add(prag)
    return None

def flatten(file_path: str, seen: Optional[Set[str]] = None, seen_meta=None) -> FlattenSourceResult:
    '''
    Flatten a contract recursively. Return a list of tuple with three elements:
    - `file_path` file path the current line belongs to
    - `linenum` the line numer in the file.
    - `line` the content of the line with the trailing line break

    Note all line numbers here are zero-based
    '''
    seen_meta = seen_meta or set()
    seen = seen or set()
    if file_path in seen:
        return []

    if not os.path.isfile(file_path):
        raise FlattenError(f'Target is not a file: {file_path}')

    if not file_path.lower().endswith('.sol'):
        raise FlattenError(f'Only solidity file is allowed: {file_path}')

    seen.add(file_path)
    content = []

    for linenum, line in enumerate(open(file_path, 'r')):
        segs = line.strip().split(maxsplit=1)
        if segs and segs[0] == 'import':
            quote = segs[1][0]
            path = segs[1][:-1].strip(quote)
            print(f'{file_path} {path}')
            path = abspath(os.path.join(Path(file_path).parent, path))
            content = content + flatten(path, seen, seen_meta)
        else:
            nline = segs and (replace_pragma(seen_meta, F_PRGAMA_ABICODER, *segs) or
                              replace_pragma(seen_meta, F_PRGAMA_ABICODERV2, *segs) or
                              replace_pragma(seen_meta, F_PRGAMA_SMTCHECKER, *segs) or
                              replace_spdx(line))
            nl = nline or line
            # a source code file can end without a line break, need to append one
            nl = nl if nl.endswith('\n') else f'{nl}\n'
            content.append((abspath(file_path), linenum, nl))
            # print('{:2d} {} {}'.format(linenum, nl, nl.endswith("\n")))
    return content


def reverse_line_lookup(flatten_lines: FlattenSourceResult, linenum: int) -> FlattenLine:
    return flatten_lines[linenum]

class FlattenSolidity():
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    @cached_property
    def flatten_result(self) -> FlattenSourceResult:
        '''
        Flattened lines containing line number and file paths mapping information between input and output lines 
        '''
        return flatten(self.file_path)

    @cached_property
    def flatten_source(self) -> str:
        '''
        Flattened source code which can be passed directly to a solc compiler
        '''
        return ''.join((c[2] for c in self.flatten_result))

    def reverse_line_lookup(self, linenum) -> FlattenLine:
        '''
        Given a line number in the flattend source code, returns the file path and the line number this line is from
        '''
        return self.flatten_result[linenum]
        

