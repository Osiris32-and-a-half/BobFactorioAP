from .GameRecipe import GameRecipe
from .Utils import DefinitionSource


class GameItem:
    def __init__(self, name: str, source = DefinitionSource.UNKNOWN):
        self.name = name
        self.source = source
        self.logic_info: dict[str, ...] = {}

        self.crafted_in: set[GameRecipe] = set()
        self.used_in: set[GameRecipe] = set()
