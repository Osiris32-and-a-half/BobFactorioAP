from enum import Enum


class DefinitionSource(Enum):
    UNKNOWN = 0
    EXTRACTED = 1
    CUSTOM = 2
    IMPLIED = 3
    WORLD = 4
