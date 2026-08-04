from __future__ import annotations

from typing import Callable

from .BaseComponent import BaseComponent

from ..Nodes import Node, AndNode, OrNode


class MultiLogicComponent(BaseComponent):
    def __init__(self, node: Node):
        super().__init__(node)

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

        for callback in self.callbacks:
            callback(self.owner)

    def test_enable(self):
        self.__pre_test_enable()
        self.__test_enable()
        self.__post_test_enable()

    def __pre_test_enable(self):
        self.in_update: bool = True

    def __test_enable(self):
        raise NotImplementedError(f"{self.__class__.__name__} not implemented.")

    def __post_test_enable(self):
        self.in_update: bool = False

    def disable(self):
        self.manual_path = False
        for node in self.owner.used_by:
            external_logic: BaseLogic = node.get_component(MultiLogicComponent).worlds[self.slotID]
            if not node.manual and (external_logic.manual_path is True or external_logic.manual_path is self.owner):
                external_logic.__disable()
            if external_logic.automate_path is True or external_logic.automate_path is self.owner:
                external_logic.__automate_disable()

    def __disable(self):
        self.disable()
        self.test_enable()

    def automate_disable(self):
        self.automate_path = False
        for node in self.owner.used_by:
            external_logic: BaseLogic = node.get_component(MultiLogicComponent).worlds[self.slotID]
            if external_logic.automate_path is True or external_logic.automate_path is self.owner:
                external_logic.__automate_disable()

    def __automate_disable(self):
        self.automate_disable()
        self.test_enable()


class AnyLogic(BaseLogic):
    def __test_enable(self) -> bool:
        if self.automate_path:
            return False

        def propagate_update():
            for node in self.owner.used_by.keys():
                node.get_component(MultiLogicComponent).worlds[self.slotID].test_enable()

        if self.owner.manual and not self.manual_path:
            self.manual_path = True
            propagate_update()
            if self.automate_path:
                return True

        if isinstance(self.owner, AndNode):
            automateable = True
            for node in self.owner.required:
                external_logic = node.get_component(MultiLogicComponent).worlds[self.slotID]
                if external_logic.automate_path:
                    continue
                elif external_logic.manual_path:
                    if self.owner.manual:
                        continue
                    if self.manual_path:
                        return False
                    automateable = False
                else:
                    return False

            if automateable:
                self.automate_path = True
            else:
                self.manual_path = True

            propagate_update()

            return True
        elif isinstance(self.owner, OrNode):
            manual_path = None
            for node in self.owner.required:
                external_logic = node.get_component(MultiLogicComponent).worlds[self.slotID]
                if external_logic.automate_path:
                    self.automate_path = node
                    propagate_update()
                    return True
                elif not self.manual_path and external_logic.manual_path:
                    manual_path = node

            if manual_path:
                if self.owner.manual:
                    self.automate_path = manual_path
                else:
                    self.manual_path = manual_path
                propagate_update()
                return True
        else:
            self.automate_path = True
            propagate_update()
            return True
        return False