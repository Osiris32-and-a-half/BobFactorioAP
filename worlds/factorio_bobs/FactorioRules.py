from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, override

from rule_builder.rules import Has, Rule, And, Or
from . import FactorioModpack
from .RecipeEngine.NodeComponents.LogicComponents import BaseLogic, MultiLogicComponent
from .RecipeEngine.Nodes import Node

if TYPE_CHECKING:
    from . import FactorioBobs
    from BaseClasses import CollectionState

@dataclasses.dataclass()
class NodeRule(Rule[FactorioBobs], game="Factorio Modpacks"):
    def __init__(self, item: Node):
        super().__init__()
        self.node = item
        assert self.node.get_component(MultiLogicComponent)


    @override
    def _instantiate(self, world: FactorioBobs) -> Rule.Resolved:
        # caching_enabled only needs to be passed in when your world inherits from CachedRuleBuilderWorld
        component: MultiLogicComponent = self.node.get_component(MultiLogicComponent)
        return self.Resolved(component.worlds[world.player], player=world.player, caching_enabled=False)

    class Resolved(Rule.Resolved):
        logic: BaseLogic

        @override
        def _evaluate(self, state: CollectionState) -> bool:
            return bool(self.logic.automate_path)

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
        return NodeRule(modpack.game_item_manager.get_item_node(rule_value))
    if rule_type == "recipe":
        # assert rule_value in modpack.game_item_manager.recipes.keys(), f"{rule_value} is not a valid recipe in rules"
        return NodeRule(modpack.game_item_manager.get_recipe_node(rule_value))
    raise ValueError(f"Unknown rule type {rule_type}")