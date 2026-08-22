from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, override

from rule_builder.rules import Has, Rule, And, Or
from worlds.AutoWorld import LogicMixin
from . import FactorioModpack
from .RecipeEngine.NodeComponents.LogicComponents import BaseLogic, MultiLogicComponent
from .RecipeEngine.Nodes import Node, OrNode, AndNode

if TYPE_CHECKING:
    from . import FactorioBobs
    from BaseClasses import CollectionState, MultiWorld


class GraphRuleContainer(LogicMixin):
    node_logic: dict[int, dict[Node, BaseLogic]]

    def init_mixin(self, multiworld: MultiWorld) -> None:
        self.node_logic = {}
        for world in multiworld.get_game_worlds("Factorio Modpacks"):
            player = world.player
            if world.modpack:
                self.node_logic[player] = {node: AnyLogic(node, player, self)
                             for node in world.modpack.game_item_manager.recipe_engine.nodes.values()}
                character_logic: BaseLogic = self.node_logic[player][world.modpack.game_item_manager.character_node]
                character_logic.manual_path = True
                character_logic.propagate_update()
            else:
                self.node_logic[player] = {}

    def copy_mixin(self, new_state: CollectionState) -> CollectionState:
        # Be careful to make a "deep enough" copy here!
        new_state.node_logic = {
            player: {node: logic.copy(new_state)
                     for node, logic in all_nodes.items()} for player, all_nodes in self.node_logic.items()
        }
        return new_state

class BaseLogic:
    def __init__(self, owner: Node, slotID: int, state: CollectionState):
        self.owner = owner
        self.slotID = slotID
        self.state = state

        self.in_update: bool = False

        # If on `and` node should be bool, if on `or` should be Node or false
        self.__automate_path: Node | bool = False
        # If on `and` node should be bool, if on `or` should be Node or false
        self.__manual_path: Node | bool = False

    def copy(self, new_state: CollectionState):
        new_copy = type(self)(self.owner, self.slotID, new_state)

        new_copy.__manual_path = self.__manual_path
        new_copy.__automate_path = self.__automate_path
        return new_copy

    @property
    def automate_path(self) -> Node | bool:
        return self.__automate_path

    @automate_path.setter
    def automate_path(self, value: Node | bool):
        self.__automate_path = value
        #
        # if value:
        #     print(f"in: {self.owner.name}")
        # else:
        #     print(f"out: {self.owner.name}")

        if value and not self.manual_path:
            self.manual_path = value
            return # manual_path setter does call back

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
            external_logic: BaseLogic = self.state.node_logic[self.slotID][node]
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
            external_logic: BaseLogic = self.state.node_logic[self.slotID][node]
            if external_logic.automate_path is True or external_logic.automate_path is self.owner:
                dependencies.update(external_logic.get_automate_dependencies())

        return dependencies

    def force_enable(self):
        self.automate_path = True
        self.propagate_update()

    def propagate_update(self):
        for node in self.owner.used_by.keys():
            self.state.node_logic[self.slotID][node].test_enable()

class AnyLogic(BaseLogic):
    @override
    def _test_enable(self) -> bool:
        if self.automate_path:
            return False

        if isinstance(self.owner, AndNode):
            automateable = True
            for node in self.owner.required:
                external_logic = self.state.node_logic[self.slotID][node]
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
                external_logic = self.state.node_logic[self.slotID][node]
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

@dataclasses.dataclass()
class AutomateNodeRule(Rule["FactorioBobs"], game="Factorio Modpacks"):
    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        assert self.node.get_component(MultiLogicComponent)


    @override
    def _instantiate(self, world: FactorioBobs) -> Rule.Resolved:
        # caching_enabled only needs to be passed in when your world inherits from CachedRuleBuilderWorld
        return self.Resolved(self.node, player=world.player, caching_enabled=False)

    class Resolved(Rule.Resolved):
        node: Node

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            return bool(state.node_logic[self.player][self.node].automate_path)

@dataclasses.dataclass()
class ManualNodeRule(Rule["FactorioBobs"], game="Factorio Modpacks"):
    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        assert self.node.get_component(MultiLogicComponent)


    @override
    def _instantiate(self, world: FactorioBobs) -> Rule.Resolved:
        # caching_enabled only needs to be passed in when your world inherits from CachedRuleBuilderWorld
        return self.Resolved(self.node, player=world.player, caching_enabled=False)

    class Resolved(Rule.Resolved):
        node: Node

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            return bool(state.node_logic[self.player][self.node].manual_path)


def process_yaml_rule(rule_pair: dict[str, str | list], modpack: FactorioModpack) -> Rule:
    rule_type, rule_value = next(iter(rule_pair.items()))
    if rule_type == "and":
        return And(*(process_yaml_rule(rule, modpack) for rule in rule_value))
    if rule_type == "or":
        return Or(*(process_yaml_rule(rule, modpack) for rule in rule_value))
    if rule_type == "tech":
        assert rule_value in modpack.base_technology_table.keys(), f"{rule_value} is not a valid tech for rules"
        return Has(rule_value)
    if rule_type == "item":
        # assert rule_value in modpack.game_item_manager.game_items.keys(), f"{rule_value} is not a valid item in rules"
        return AutomateNodeRule(modpack.game_item_manager.get_item_node(rule_value))
    if rule_type == "recipe":
        # assert rule_value in modpack.game_item_manager.recipes.keys(), f"{rule_value} is not a valid recipe in rules"
        return AutomateNodeRule(modpack.game_item_manager.get_recipe_node(rule_value))
    raise ValueError(f"Unknown rule type {rule_type}")