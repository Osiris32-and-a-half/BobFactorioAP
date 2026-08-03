from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from ..Nodes import Node

class BaseComponent:
    def __init__(self, owner: "Node"):
        self.owner: "Node" = owner