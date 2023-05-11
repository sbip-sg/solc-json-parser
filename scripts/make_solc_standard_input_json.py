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

def generate_solc_json(input_directory, output_file):
    sol_files = find_sol_files(input_directory)

    solc_input = {
        "language": "Solidity",
        "sources": {},
        "settings": {
            "outputSelection": OUTPUT_SELECT_ALL
        }
    }

    for sol_file in sol_files:
        with open(sol_file, 'r') as file:
            content = file.read()
        solc_input["sources"][sol_file] = {"content": content}

    with open(output_file, 'w') as file:
        json.dump(solc_input, file, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate solc standard JSON input.")
    parser.add_argument('input_directory', type=str, help='Input directory path')
    parser.add_argument('output_file', type=str, help='Output JSON file path')
    args = parser.parse_args()

    generate_solc_json(args.input_directory, args.output_file)
