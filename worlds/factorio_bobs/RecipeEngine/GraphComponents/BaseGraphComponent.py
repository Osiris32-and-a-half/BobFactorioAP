from __future__ import annotations

import typing

from ..Nodes import Node

if typing.TYPE_CHECKING:
    from ..Graph import Graph

class BaseGraphComponent:
    def __init__(self, owner: Graph):
        self.owner: Graph = owner

    def on_node_init(self, node: Node):
        pass