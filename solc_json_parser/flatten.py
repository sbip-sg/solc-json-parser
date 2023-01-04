from dataclasses import dataclass
from dataclasses import asdict
from typing import List, Optional, Set
import os
from pathlib import Path
from os.path import abspath
from functools import cache
import argparse
import json
import re

# Duplicate pragma to be dropped
F_PRGAMA_ABICODER = 'abicoder'
F_PRGAMA_ABICODERV2 = 'ABIEncoderV2'
F_PRGAMA_SMTCHECKER = 'SMTChecker'

INSTALLABLE_VERSION = []

class FlattenError(ValueError):
    pass

@dataclass
class FlattenLine():
    path: str
    filename: str
    sourceLineNum: int
    sourceLine: str
    targetLineNum: int
    targetLine: str

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

get_file_name = lambda p: p.split(os.path.sep)[-1]
quotes = '"\'' # solidity quote characters

class FlattenSolidity():
    def __init__(self, file_path: str, include_paths: List[str] = []) -> None:
        self.file_path = file_path
        self.seen = set()
        self.seen_meta = set()
        self.include_paths = include_paths or []
        self.targetLineNum = 0
        self.content = []
        self.isImport = False

    def hasQuote(self, line: str) -> bool:
        for c in quotes:
            if c in line:
                return True
        return False

    def searchAndFlatten(self, path):
        found_import = False
        if os.path.isfile(path):
            found_import = True
        for include_path in self.include_paths:
            if os.path.isfile(include_path+'/'+path):
                path = include_path + '/' + path
                found_import = True
        if not found_import:
            raise FlattenError(f'Cannot find import file: {path}')
        # path = abspath(os.path.join(Path(file_path).parent, path))
        self.flatten(path)

    def appendFlattenLine(self, path, filename, srcLineNum, srcLine, targetLine):
        fline = FlattenLine(path, filename, srcLineNum, srcLine, self.targetLineNum, targetLine)
        self.targetLineNum += 1
        self.content.append(fline)

    def handlePendingImport(self, line, path, filename, linenum):
        if not self.isImport:
            return False

        self.appendFlattenLine(abspath(path), filename, linenum, line, f"// {line}")

        if not self.hasQuote(line):
            return True
        else:
            # path = line.split('"')[-2].strip('"')
            path = re.split(r'[\'"]', line)[-2].strip(quotes)
            self.isImport = False
            self.searchAndFlatten(path)
            return True

    def handleImport(self, line, path, filename, linenum) -> bool:
        segs = line.strip().split(maxsplit=1)
        if not (segs and segs[0] == 'import'):
            return False

        if '{' in segs[1]:
            if '"' in line:
                path = line.split('"')[-2].strip('"')
                self.searchAndFlatten(path)
                return True
            else:
                self.isImport = True
                self.appendFlattenLine(abspath(path), filename, linenum, line,  f"// {line}")
                return True
        else:
            quote = segs[1][0]
            path = segs[1][:-1].strip(quote)
            self.appendFlattenLine(abspath(path), filename, linenum, line, f"// {line}")
            self.searchAndFlatten(path)
            return True

    def handleLine(self, line, path, filename, linenum) -> bool:
        segs = line.strip().split(maxsplit=1)
        nl = line
        if segs:
            nl = replace_pragma(self.seen_meta, F_PRGAMA_ABICODER, *segs) \
                or replace_pragma(self.seen_meta, F_PRGAMA_ABICODERV2, *segs) \
                or replace_pragma(self.seen_meta, F_PRGAMA_SMTCHECKER, *segs) \
                or replace_spdx(line) \
                or line
        # a source code file can end without a line break, need to append one
        nl = nl if nl.endswith('\n') else f'{nl}\n'
        self.appendFlattenLine(abspath(path), filename, linenum, line, nl)
        return True

    def flatten(self, file_path: str):
        '''
        Flatten a contract recursively. Return a list of tuple with three elements:
        - `file_path` path of current line
        - `linenum` the line numer in the file.
        - `line` the content of the line with the trailing line break

        Note all line numbers here are zero-based
        '''
        seen = self.seen
        include_paths = self.include_paths

        file_name = get_file_name(os.path.abspath(file_path))

        if file_name in seen:
            return

        if not os.path.isfile(file_path):
            raise FlattenError(f'Target is not a file: {file_path}')

        if not file_path.lower().endswith('.sol'):
            raise FlattenError(f'Only solidity file is allowed: {file_path}')
        include_paths.append(abspath(os.path.join(Path(file_path).parent)))
        # NOTE here we assume same file name at different places on the file system represent the same file
        seen.add(file_name)

        with open(file_path, 'r') as f:
            for linenum, line in enumerate(f):
                args = [line, file_path, file_name, linenum]
                _ = self.handlePendingImport(*args) or self.handleImport(*args) or self.handleLine(*args)

    @cache
    def flatten_result(self) -> FlattenSourceResult:
        '''
        Flattened lines containing line number and file paths mapping information between input and output lines
        '''
        self.flatten(self.file_path)
        return self.content

    @cache
    def flatten_source(self) -> str:
        '''
        Flattened source code which can be passed directly to a solc compiler
        '''
        return ''.join(c.targetLine for c in self.flatten_result())

    def reverse_line_lookup(self, linenum) -> FlattenLine:
        '''
        Given a line number in the flattend source code, returns the file path and the line number this line is from
        '''
        return self.flatten_result()[linenum]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, help='The main contract to be flattened', required=True)
    parser.add_argument('--include', action='append', help='The paths of included libraries to be flattened', required=False)
    parser.add_argument('--output', type=str, help='The output path to write file', required=False)
    parser.add_argument('--json-output', type=str, help='The json output file saving the line mapping information', required=False)
    args = parser.parse_args()

    path = args.path
    include_paths = args.include or []
    for i in range(len(include_paths)):
        if include_paths[i][-1] == '/':
            include_paths[i] = include_paths[i][:-1]

    if not os.path.exists(path):
        raise Exception(f'File not found {path}')

    if not os.path.isfile(path):
        raise Exception(f'Target is not file {path}')

    fs = FlattenSolidity(path, include_paths = include_paths)

    content = ''.join([fl.targetLine for fl in fs.flatten_result()])

    filename = path.split(os.path.sep)[-1]
    ext = filename.split('.')[-1]
    output = args.output or (filename[:-len(ext)-1] + '_flattened.' + ext)
    json_output = args.json_output or (filename[:-len(ext)-1] + '_flattened.json')

    with open(output, 'w') as f:
        f.write(content)

    with open(json_output, 'w') as f:
        r = [asdict(e) for e in fs.flatten_result()]
        f.write(json.dumps(r))

if __name__ == '__main__':
    main()
