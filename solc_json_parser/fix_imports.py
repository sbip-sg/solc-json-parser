# Fix imports path for all solidity files in the `--root` directory
# Use this script to make the source code compilable. Assuming all source code are in the root directory.

import re
import os
from typing import Optional, Set

# 4 kinds of import directives as regex
# use this to extract the `path` or `unit name`
RE_IMPORT_SIMPLE = re.compile(r'''import\s+['"](.*\.sol)['"];''')
RE_IMPORT_AS = re.compile(r'''import\s+['"](.*\.sol)['"]\s+as\s+\w+;''')
RE_IMPORT_AS_FROM = re.compile(r'''import\s+.*\s+as\s+.*\s+from\s+['"](.*\.sol)['"];''')
RE_IMPORT_FROM = re.compile(r'''import\s+.*\s+from\s+['"](.*\.sol)['"];''')

# When searching for candidate matching a contract in source code,
# this allows a prefix in the candidate contract file names
RE_ALLOWED_FILE_PREFIX = re.compile(r'^\d+_\d+_(.*\.sol)$')

def search_sol_by_filename(name: str, candidates: Set[str]) -> str:
    if name in candidates:
        return name

    for f in candidates:
        found = RE_ALLOWED_FILE_PREFIX.findall(f)
        
        if found and found[0] == name:
            return f

    raise Exception(f'No candidate contract found for {name}')

def sol_in_line(line: str) -> Optional[str]:
    '''
    Extract the relative path or the unit name from an `import` directive
    '''
    line = line.strip();
    found = RE_IMPORT_AS.findall(line) \
        or RE_IMPORT_AS_FROM.findall(line) \
        or RE_IMPORT_SIMPLE.findall(line) \
        or RE_IMPORT_FROM.findall(line)

    if len(found) > 0:
        return found[0]
    return None

def to_simple_name(path: str)-> str:
    '''
    Returns a filename by removing any path prefixes
    '''
    return path.split(r'/')[-1]

def fix_import_line(line: str, candidates: Set[str]) -> str:
    sol = sol_in_line(line)
    replacement =  search_sol_by_filename(to_simple_name(sol), candidates) if sol else None

    if replacement:
        nline = line.replace(sol, f'./{replacement}')
        # print(f'{line} -> {nline}')
        return nline

    return line


def fix_import(sol, candidates):
    lines = []
    with open(sol, 'r') as f:
        lines = list(f.readlines())

    updated_lines = [fix_import_line(line, candidates) for line in lines]
    if lines != updated_lines:
        with open(sol, 'w') as f:
            f.write(''.join(updated_lines))


def fix_imports_inplace(root: str):
    sols =  [os.path.join(root, f) for f in os.listdir(root) if f.endswith('.sol')]
    candidates = set([p.split(os.path.sep)[-1] for p in sols])
    if len(candidates) != len(sols):
        raise Exception('Duplicate file names found in folder, we can not handle this case yet!')

    for f in sols:
        fix_import(f, candidates)



if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, help="Root directory of a single solidity project", required=True)
    args = ap.parse_args()
    root = args.root
    fix_imports_inplace(root)
