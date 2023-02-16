from typing import Set
try:
    from solc_json_parser import opcodes
except:
    import opcodes

def abi_from_binary(binary: str, window_size=20) -> Set[str]:
    results = set()
    length = len(binary)
    i = 0
    window_start, confidence, candidate = (0, 0, '')

    while i < length:
        # get opcode string
        opcode = opcodes.byte_to_name.get(int(binary[i:i+2], 16))
        i += 2

        # ignore unknown opcode
        if not opcode:
            continue

        # for push opcode, skip data bytes
        if opcode.startswith('PUSH'):
            datasize = int(opcode[4:]) * 2

            # for push4, record the 4 byte hex string which might be a function signature
            if datasize == 8:
                candidate = binary[i: i + datasize]
                window_start = i
                confidence += 1

            i += datasize
        elif opcode == 'EQ' and window_start:
            confidence += 1
        elif opcode == 'JUMPI' and window_start:
            if confidence > 1:
                results.add(candidate)
            window_start, confidence, candidate = (0, 0, '')


        if i - window_start > window_size:
            window_start = 0

    results.remove('ffffffff')
    return results
