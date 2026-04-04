from .Nodes import Node
from .Utils import DefinitionSource


class RecipeEngineCore:
    num_unnamed_nodes = 0

    def __init__(self):
        self.nodes = {}

    def add_node(self, node: Node):
        if node.name in self.nodes:
            raise RuntimeError(f"Node ({node.name}) already exists")
        self.nodes[node.name] = node
