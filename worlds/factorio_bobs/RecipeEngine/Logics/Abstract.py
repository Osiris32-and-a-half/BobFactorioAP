from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..RecipeEngineCore import RecipeEngineCore


class AbstractNodeContainer:
    LOGIC_NAME = "Abstract"

class AbstractLogic:
    name = "Abstract"
    node_container = AbstractNodeContainer

    def __init_subclass__(cls, **kwargs):
        logics.add(cls)

    def run(self, core: "RecipeEngineCore") -> None:
        pass


logics: set[type[AbstractLogic]] = set()
