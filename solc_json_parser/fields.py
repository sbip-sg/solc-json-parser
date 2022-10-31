from dataclasses import dataclass
from typing import List

@dataclass
class Field:
    inherited_from:   str
    visibility: str
    name:       str
    line_num:   tuple # (start, end)


@dataclass
class Function:
    raw: str
    inherited_from:   str
    abstract:    bool
    visibility:  str
    signature:   str
    return_signature: str
    name:        str
    modifiers:   list
    kind:        str
    state_mutability: str
    line_num: tuple  # (start, end)


@dataclass
class ContractData:
    abstract:       bool
    name:           str
    kind:           str
    base_contracts: List[int]
    fields:         list
    functions:      list
    modifiers:      list
    line_num:       tuple # (start, end)
    contract_id: int # unique id in ast per solc compilation

@dataclass
class Modifier:
    name: str
    visibility: str





# [Function(signature='',           return_signature='',   name='receive',  modifiers=[], type='receive'),
#  Function(signature='receive()',  return_signature='()', name='receive',  modifiers=[], type='function'),
#  Function(signature='fallback()', return_signature='()', name='fallback', modifiers=[], type='function'),
#  Function(signature='',           return_signature='',   name='fallback', modifiers=[], type='fallback')]