from dataclasses import dataclass

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
    line_num:    tuple # (start, end)


@dataclass
class ContractData:
    abstract:       bool
    name:           str
    kind:           str
    base_contracts: list
    fields:         list
    functions:      list
    modifiers:      list
    line_num:       tuple # (start, end)

@dataclass
class Modifier:
    name: str
    visibility: str
