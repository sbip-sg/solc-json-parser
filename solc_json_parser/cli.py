#!/usr/bin/env python3
import argparse
from . import opcodes

def main():
    parser = argparse.ArgumentParser(description='CLI tool description.')
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')
    decode_parser = subparsers.add_parser('decode_binary', aliases=['dp'], help='Decode binary data')
    decode_parser.add_argument('data', type=str, help='Binary data to decode')

    args = parser.parse_args()

    if args.command in ['decode_binary', 'dp']:
        opcodes.decode_and_print(args.data)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
