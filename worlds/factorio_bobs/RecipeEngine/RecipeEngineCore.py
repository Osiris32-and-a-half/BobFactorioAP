from .Nodes import Node


class RecipeEngineCore:
    num_unnamed_nodes = 0

    def __init__(self):
        self.nodes: dict[str, Node] = {}

    def add_node(self, node: Node):
        if node.name in self.nodes:
            raise RuntimeError(f"Node ({node.name}) already exists")
        self.nodes[node.name] = node
