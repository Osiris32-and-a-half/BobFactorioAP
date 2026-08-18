from typing import TypeVar, Generic

from .GraphComponents import BaseGraphComponent
from .Nodes import Node

T = TypeVar("T", bound=BaseGraphComponent)
N = TypeVar("N", bound=Node)

class Graph(Generic[T]):
    def __init__(self):
        self.nodes: dict[str, Node] = {}

        self.__components: dict[type[T], T] = {}

    def add_node(self, node: N) -> N:
        if node.name in self.nodes:
            raise RuntimeError(f"Node ({node.name}) already exists")
        self.nodes[node.name] = node

        for component in self.__components:
            component.on_node_init(node)

        return node

    def register_component(self, component_class: type[T]) -> T:
        if component_class in self.__components:
            raise RuntimeError(f"{self} tried to register {component_class.__name__} twice")
        self.__components[component_class] = component_class(self)
        return self.__components[component_class]

    def get_component(self, component_class: type[T]) -> T:
        if component_class not in self.__components:
            raise RuntimeError(f"tried to get {component_class} from {self}, but {component_class} was not found")
        return self.__components[component_class]