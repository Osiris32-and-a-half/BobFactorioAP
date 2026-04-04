from .Abstract import AbstractLogic, AbstractNodeContainer
from ..Nodes import Node
from ..RecipeEngineCore import RecipeEngineCore

class MinimumContainer(AbstractNodeContainer):
    LOGIC_NAME = "Minimum"
    def __init__(self):
        self.manual_steps = float("inf")
        self.automatic_steps = float("inf")

        self.manual_direction: None | Node = None
        self.automatic_direction: None | Node = None

class MinimumLogic(AbstractLogic):
    OTHER_LOGIC_REQUIRED = set()

    def run(self, core: "RecipeEngineCore") -> None:
        pass