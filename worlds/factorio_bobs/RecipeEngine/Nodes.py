from typing import TypeVar, Generic

from .Components.BaseComponent import BaseComponent
from .Logics.Abstract import AbstractNodeContainer

T = TypeVar("T", bound=BaseComponent)

class Node(Generic[T]):
    LOGIC_CONTAINER_CLASSES = set()
    def __init__(self, name: str):
        self.name = name

        # How many of the nodes can be created from 1 of this one
        # 0 Can be used to denote that it's used as a catalyst
        self.used_by: dict[Node, float] = {}

        # set of nodes that can make node
        # need to be updated for backword propagation
        self.required: set[Node] = set()

        # this is the cost of using this node itself for any generic cost algorithm
        self.cost = 0

        # A location for logic to store information per node
        self.logic: dict[str, AbstractNodeContainer] = {}
        for logic_container_class in Node.LOGIC_CONTAINER_CLASSES:
            self.logic[logic_container_class.LOGIC_NAME] = logic_container_class()

        # Can spontaneously crate node however all usage is classed as manual
        # usage classification changes if all `required` aren't manual and another option for the node is available when catalyst
        self.manual: bool = False

        self.__components: dict[type[T], T] = {}

    def __repr__(self):
        return f"{type(self)}({self.name})"

    def valid_with(self, nodes: set["Node"]) -> bool:
        return False

    def add_used_by(self, node: "Node", quantity: float|None):
        self._add_used_by(node, quantity)
        node._add_required(self)

    def _add_used_by(self, node: "Node", quantity: float|None):
        if node in self.used_by:
            raise RuntimeError(f"{self} tried to add {node} when it's already used")
        self.used_by[node] = quantity

    def remove_used_by(self, nodes: None | set["Node"]=None):
        if nodes is None:
            nodes = self.required.copy()
        for node in nodes:
            node._remove_required(self)
            self._remove_used_by(node)

    def _remove_used_by(self, node: "Node"):
        if node not in self.used_by:
            raise RuntimeError(f"{self} tried to remove {node} when it's not used")
        del self.used_by[node]

    def add_required(self, node: "Node", quantity: float|None):
        self._add_required(node)
        if quantity is None or quantity == 0:
            node._add_used_by(self, None)
        else:
            node._add_used_by(self, 1/quantity)

    def _add_required(self, node: "Node"):
        if node in self.required:
            raise RuntimeError(f"{self} tried to add {node} when it's already required")
        self.required.add(node)

    def remove_required(self, nodes: None | set["Node"]=None):
        if nodes is None:
            nodes = self.required.copy()
        for node in nodes:
            node._remove_used_by(self)
            self._remove_required(node)

    def _remove_required(self, node: "Node"):
        if node not in self.required:
            raise RuntimeError(f"{self} tried to remove {node} when it's not required")
        self.required.remove(node)

    def register_component(self, component_class: type[T], instance: T):
        if component_class in self.__components:
            raise RuntimeError(f"{self} tried to register {component_class} twice")
        self.__components[component_class] = instance

    def get_component(self, component_class: type[T]) -> T:
        if component_class not in self.__components:
            raise RuntimeError(f"tried to get {component_class} from {self}, but {component_class} was not found")
        return self.__components[component_class]


class AndNode(Node):
    def __init__(self, name: str):
        super().__init__(name)

    def valid_with(self, nodes: set["Node"]) -> bool:
        for required in self.required:
            if required not in nodes:
                return False
        return True

class OrNode(Node):
    def __init__(self, name: str):
        super().__init__(name)

    def valid_with(self, nodes: set["Node"]) -> bool:
        for required in self.required:
            if required in nodes:
                return True
        return False

class ItemNode(OrNode):
    def __init__(self, name: str):
        super().__init__(name)

class RecipeNode(AndNode):
    def __init__(self, name: str):
        super().__init__(name)