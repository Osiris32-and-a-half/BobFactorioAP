from .GameItem import GameItem
from .Utils import DefinitionSource


class GameRecipe:
    def __init__(self, name: str, source = DefinitionSource.UNKNOWN):
        self.name = name
        self.source = source
        self.logic_info: dict[str, ...] = {}

        self.ingredients: dict[GameItem, int] = {}
        self.products: dict[GameItem, int] = {}

        # this will be something to do with unlock tech
        self.unlock_requirements = None
        # this will be rule for item requirements
        self.crafting_requirements = None