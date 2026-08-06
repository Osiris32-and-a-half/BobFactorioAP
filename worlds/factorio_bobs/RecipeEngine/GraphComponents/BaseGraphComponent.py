from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from ..Graph import Graph

class BaseGraphComponent:
    def __init__(self, owner: Graph):
        self.owner: Graph = owner