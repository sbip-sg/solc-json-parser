# Fix imports path for all solidity files in the `--root` directory
# Use this script to make the source code compilable. Assuming all source code are in the root directory.

import re
import os
import shutil

def search_sol_in_lib_with_copying(cwd: str, file_name: str, lib_sol: str):
    if lib_sol.startswith('@'):
        lib = f'node_modules/{lib_sol}'
        if os.path.exists(lib):
            target = f'{cwd}/{file_name}'
            if not os.path.exists(target):
                shutil.copyfile(lib, target)
            return file_name
    return None


def search_sol_in_lib(cwd: str, lib_sol: str):
    if lib_sol.startswith('@'):
        lib = f'node_modules/{lib_sol}'
        if os.path.exists(lib):
            p = os.path.relpath(lib, cwd)
            return p
    return None

def search_sol_by_filename(cwd, name, complete_sol, sols):
    file_name = lambda p: p.split(os.path.sep)[-1]

    for f in sols:
        fname = file_name(f)
        # most of the filename has the format of `dd_dd_wwww.sol`
        # but sometimes it can be `dd(d)_ddd_wwww.sol`, e.g. `101_155_ERC20.sol` or `10_155_ERC20.sol`

        # find the position of second `_`
        pos = fname.find('_', fname.find('_') + 1) + 1

        if name in [fname, fname[pos:]]:
            return fname

    return search_sol_in_lib(cwd, complete_sol)

def fix_import_line(f, line, sols):
    # match = re.search(r'''['"].*/(\w+\.sol)['"];''', line)
    match = re.search(r'''["'](.*\.sol)["']''', line)
    cwd = os.path.dirname(f)
    if match:
        complete_sol = match.group(1)
        sol = complete_sol.split('/')[-1]
        replacement = search_sol_by_filename(cwd, sol, complete_sol, sols)
        if replacement:
            nline = f'import "./{replacement}";\n'
            # print(f'{line} -> {nline}')
            return nline

    return line


def fix_import(sol, sols):
    lines = []
    with open(sol, 'r') as f:
        lines = list(f.readlines())

    updated_lines = [fix_import_line(sol, line, sols) for line in lines]
    if lines != updated_lines:
        with open(sol, 'w') as f:
            f.write(''.join(updated_lines))



if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, help="Root directory of a single solidity project")
    args = ap.parse_args()
    root = args.root
    sols =  [os.path.join(root, f) for f in os.listdir(root) if f.endswith('.sol')]
    for f in sols:
        fix_import(f, sols)
