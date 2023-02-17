# This script guesses the function signatures from a compiled contract binary.
#
# Function signatures have the pattern PUSH4 [4-byte fn_sig] EQ ... JUMPI pattern (Thanks @minhhn2910)
# Example from https://ethervm.io/decompile/0x5a98fcbea516cf06857215779fd812ca3bef1b32:
#
# label_0000:
# 	// Inputs[1] { @0007  msg.data.length }
# 	0000    60  PUSH1 0x80
# 	0002    60  PUSH1 0x40
# 	0004    52  MSTORE
# 	0005    60  PUSH1 0x04
# 	0007    36  CALLDATASIZE
# 	0008    10  LT
# 	0009    61  PUSH2 0x0148
# 	000C    57  *JUMPI
# 	// Stack delta = +0
# 	// Outputs[1] { @0004  memory[0x40:0x60] = 0x80 }
# 	// Block ends with conditional jump to 0x0148, if msg.data.length < 0x04

# label_000D:
# 	// Incoming jump from 0x000C, if not msg.data.length < 0x04
# 	// Inputs[1] { @0032  msg.data[0x00:0x20] }
# 	000D    63  PUSH4 0xffffffff
# 	0012    7C  PUSH29 0x0100000000000000000000000000000000000000000000000000000000
# 	0030    60  PUSH1 0x00
# 	0032    35  CALLDATALOAD
# 	0033    04  DIV
# 	0034    16  AND
# 	0035    63  PUSH4 0x06fdde03
# 	003A    81  DUP2
# 	003B    14  EQ
# 	003C    61  PUSH2 0x0225
# 	003F    57  *JUMPI
# 	// Stack delta = +1
# 	// Outputs[1] { @0034  stack[0] = msg.data[0x00:0x20] / 0x0100000000000000000000000000000000000000000000000000000000 & 0xffffffff }
# 	// Block ends with conditional jump to 0x0225, if msg.data[0x00:0x20] / 0x0100000000000000000000000000000000000000000000000000000000 & 0xffffffff == 0x06fdde03

# label_0040:
# 	// Incoming jump from 0x003F, if not msg.data[0x00:0x20] / 0x0100000000000000000000000000000000000000000000000000000000 & 0xffffffff == 0x06fdde03
# 	// Inputs[1] { @0040  stack[-1] }
# 	0040    80  DUP1
# 	0041    63  PUSH4 0x095ea7b3
# 	0046    14  EQ
# 	0047    61  PUSH2 0x02af
# 	004A    57  *JUMPI
# 	// Stack delta = +0
# 	// Block ends with conditional jump to 0x02af, if 0x095ea7b3 == stack[-1]

# label_004B:
# 	// Incoming jump from 0x004A, if not 0x095ea7b3 == stack[-1]
# 	// Inputs[1] { @004B  stack[-1] }
# 	004B    80  DUP1
# 	004C    63  PUSH4 0x17634514
# 	0051    14  EQ
# 	0052    61  PUSH2 0x02f4
# 	0055    57  *JUMPI
# 	// Stack delta = +0
# 	// Block ends with conditional jump to 0x02f4, if 0x17634514 == stack[-1]

# label_0056:
# 	// Incoming jump from 0x0055, if not 0x17634514 == stack[-1]
# 	// Inputs[1] { @0056  stack[-1] }
# 	0056    80  DUP1
# 	0057    63  PUSH4 0x18160ddd
# 	005C    14  EQ
# 	005D    61  PUSH2 0x031b
# 	0060    57  *JUMPI
# 	// Stack delta = +0
# 	// Block ends with conditional jump to 0x031b, if 0x18160ddd == stack[-1]


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

    if 'ffffffff' in results:
        results.remove('ffffffff')
    return results
