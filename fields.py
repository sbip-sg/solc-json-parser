from dataclasses import dataclass

@dataclass
class Field:
    inherited_from:   str
    visibility: str
    name:       str


@dataclass
class Function:
    inherited_from:   str
    abstract:    bool
    visibility:  str
    signature:   str
    return_signature: str
    name:        str
    modifiers:   list


@dataclass
class ContractData:
    abstract:       bool
    name:           str
    kind:           str
    base_contracts: list
    fields:         list
    functions:      list
    modifiers:      list
    

@dataclass
class Modifier:
    name: str
    visibility: str