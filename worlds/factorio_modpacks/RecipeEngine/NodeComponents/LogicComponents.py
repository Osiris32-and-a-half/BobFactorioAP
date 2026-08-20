from __future__ import annotations

from typing import Callable, override

from .BaseNodeComponent import BaseNodeComponent

from ..Nodes import Node, AndNode, OrNode


class MultiLogicComponent(BaseNodeComponent):
    def __init__(self, node: Node):
        super().__init__(node)

        self.promotion_node = False

        self.worlds: dict[int, BaseLogic] = {}

class BaseLogic:
    def __init__(self, owner: Node, SlotID: int):
        self.owner = owner
        self.slotID = SlotID

        self.in_update: bool = False

        # If on `and` node should be bool, if on `or` should be Node or false
        self.__automate_path: Node | bool = False
        # If on `and` node should be bool, if on `or` should be Node or false
        self.__manual_path: Node | bool = False

        self.callbacks: set[Callable[[Node], None]] = set()

    @property
    def automate_path(self) -> Node | bool:
        return self.__automate_path

    @automate_path.setter
    def automate_path(self, value: Node | bool):
        self.__automate_path = value
        if value and not self.manual_path:
            self.manual_path = value
            return # manual_path setter does call back

        for callback in self.callbacks:
            callback(self.owner)

    @property
    def manual_path(self) -> Node | bool:
        return self.__manual_path

    @manual_path.setter
    def manual_path(self, value: Node | bool):
        self.__manual_path = value

        if not value and self.automate_path:
            self.automate_path = value
            return # automate_path setter does call back

        if self.owner.get_component(MultiLogicComponent).promotion_node:
            self.__automate_path = value

        for callback in self.callbacks:
            callback(self.owner)

    def test_enable(self):
        self._pre_test_enable()
        self._test_enable()
        self._post_test_enable()

    def _pre_test_enable(self):
        self.in_update: bool = True

    def _test_enable(self):
        raise NotImplementedError(f"{self.__class__.__name__} not implemented.")

    def _post_test_enable(self):
        self.in_update: bool = False

    def disable(self):
        toUpdate = self.get_dependencies()

        for node in toUpdate:
            if node.manual_path is True or node.manual_path is self.owner:
                node.manual_path = False
            elif node.automate_path is True or node.automate_path is self.owner:
                node.automate_path = False

        for node in toUpdate:
            node.test_enable()

    def get_dependencies(self) -> set[BaseLogic]:
        dependencies = self.__get_dependencies_not_including_self()
        dependencies.add(self)
        return dependencies

    def __get_dependencies_not_including_self(self) -> set[BaseLogic]:
        dependencies = set()
        for node in self.owner.used_by:
            external_logic: BaseLogic = node.get_component(MultiLogicComponent).worlds[self.slotID]
            if external_logic.manual_path is True or external_logic.manual_path is self.owner:
                dependencies.update(external_logic.get_dependencies())
            elif external_logic.automate_path is True or external_logic.automate_path is self.owner:
                dependencies.update(external_logic.get_automate_dependencies())
        return dependencies

    def get_automate_dependencies(self) -> set[BaseLogic]:
        dependencies = self.__get_automate_dependencies_not_including_self()
        dependencies.add(self)
        return dependencies

    def __get_automate_dependencies_not_including_self(self):
        dependencies = set()
        for node in self.owner.used_by:
            external_logic: BaseLogic = node.get_component(MultiLogicComponent).worlds[self.slotID]
            if external_logic.automate_path is True or external_logic.automate_path is self.owner:
                dependencies.update(external_logic.get_automate_dependencies())

        return dependencies

    def force_enable(self):
        self.automate_path = True
        self.propagate_update()

    def propagate_update(self):
        for node in self.owner.used_by.keys():
            node.get_component(MultiLogicComponent).worlds[self.slotID].test_enable()

class AnyLogic(BaseLogic):
    @override
    def _test_enable(self) -> bool:
        if self.automate_path:
            return False

        if isinstance(self.owner, AndNode):
            automateable = True
            for node in self.owner.required:
                external_logic = node.get_component(MultiLogicComponent).worlds[self.slotID]
                if external_logic.automate_path:
                    continue
                elif external_logic.manual_path:
                    if self.manual_path:
                        return False
                    automateable = False
                else:
                    return False

            if automateable:
                self.automate_path = True
            else:
                self.manual_path = True

            self.propagate_update()

            return True
        elif isinstance(self.owner, OrNode):
            manual_path = None
            for node in self.owner.required:
                external_logic = node.get_component(MultiLogicComponent).worlds[self.slotID]
                if external_logic.automate_path:
                    self.automate_path = node
                    self.propagate_update()
                    return True
                elif not self.manual_path and external_logic.manual_path:
                    manual_path = node

            if manual_path:
                self.manual_path = manual_path
                self.propagate_update()
                return True
        else:
            self.automate_path = True
            self.propagate_update()
            return True
        return False