from dataclasses import dataclass
from typing import List

@dataclass
class Field:
    inherited_from:   str
    visibility: str
    name:       str
    line_num:   tuple  # (start, end)


@dataclass
class Modifier:
    name: str
    visibility: str


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
class Event:
    name: str
    signature:  str
    anonymous: bool
    line_num: tuple
    raw: str


@dataclass
class ContractData:
    abstract:       bool
    name:           str
    kind:           str
    base_contracts: List[int]
    fields:         List[Field]
    functions:      List[Function]
    modifiers:      List[Modifier]
    line_num:       tuple  # (start, end)
    contract_id:    int    # unique id in ast per solc compilation
    events:         List[Event]





