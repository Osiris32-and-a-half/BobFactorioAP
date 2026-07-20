from .Logics.Abstract import AbstractLogic, logics
from .Nodes import Node


class RecipeEngineCore:
    num_unnamed_nodes = 0
    logics: dict[str, type[AbstractLogic]] = {}

    def __init__(self):
        self.nodes: dict[str, Node] = {}

    @staticmethod
    def register_logic(logicClass: type[AbstractLogic]):
        if logicClass.name in RecipeEngineCore.logics:
            raise RuntimeError(f"Double register logic with name: {logicClass.name}")
        RecipeEngineCore.logics[logicClass.name] = logicClass

        Node.LOGIC_CONTAINER_CLASSES[logicClass.name] = logicClass.node_container

    def add_node(self, node: Node):
        if node.name in self.nodes:
            raise RuntimeError(f"Node ({node.name}) already exists")
        self.nodes[node.name] = node

for logic in logics:
    RecipeEngineCore.register_logic(logic)