from typing import override

from .BaseGraphComponent import BaseGraphComponent
from ..Nodes import Node
from ..NodeComponents.LogicComponents import MultiLogicComponent


class GraphMultiLogic(BaseGraphComponent):
    def __init__(self, owner):
        super().__init__(owner)

        for node in self.owner.nodes.values():
            node.register_component(MultiLogicComponent)

    @override
    def on_node_init(self, node: Node):
        node.register_component(MultiLogicComponent)