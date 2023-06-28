# Converts json output from etherscan API to standard solc input json.

import os
import json

def find_sol_files(input_directory):
    sol_files = []
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            if file.endswith(".sol"):
                sol_files.append(os.path.join(root, file))
    return sol_files

OUTPUT_SELECT_ALL = {'*': {'*': [ '*' ], '': ['ast']}}

def generate_solc_json(input_file, output_file):
    with open(input_file, 'r') as f:
        api_json = json.load(f)

    solc_input = json.loads(api_json["SourceCode"].replace('{{', '{').replace('}}', '}'))
    solc_input["settings"] = {"outputSelection": OUTPUT_SELECT_ALL}

    print('Compiler version: ', api_json["CompilerVersion"])

    with open(output_file, 'w') as file:
        json.dump(solc_input, file, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate solc standard JSON input.")
    parser.add_argument('input_file', type=str, help='Input json file from etherscan API')
    parser.add_argument('output_file', type=str, help='Output JSON file path')
    args = parser.parse_args()

    generate_solc_json(args.input_file, args.output_file)
