from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .RecipeEngine.Graph import Graph
from .RecipeEngine.GraphComponents.GraphMultiLogic import GraphMultiLogic
from .RecipeEngine.NodeComponents.BaseNodeComponent import BaseNodeComponent
from .RecipeEngine.NodeComponents.LogicComponents import MultiLogicComponent
from .RecipeEngine.Nodes import ItemNode, RecipeNode, OrNode, Node, AndNode, T

if TYPE_CHECKING:
    from . import FactorioModpack

GENERATOR_ENERGY = 1

class GameItemManager:
    invalidate_cache = False

    def __init__(self, modpack: FactorioModpack):
        self.modpack = modpack
        self.name = self.modpack.packName
        self.recipe_engine = Graph()
        self.recipe_engine.register_component(GraphMultiLogic)

        self.has_init = False

        self.impossible_node = self.recipe_engine.add_node(OrNode("Impossible"))
        self.technology_nodes: dict[str, TechnologyNode] = {}
        self.fluid_mining: set[RecipeNode] = set()

        self.character_node: Node = self.recipe_engine.add_node(OrNode("Character"))

        self.__dif_entity_to_item: dict[str, str] | None = None

    def full_init(self) -> None:
        if self.has_init:
            return
        self.has_init = True

        self.__register_game_items()
        self.__register_categories()
        self.__register_recipes()
        self.__link_technologies()
        self.__load_settings()

        goal_items = {"rocket-part", "satellite", "rocket-silo"}
        randomizable_items = set(self.modpack.ordered_science_packs) | goal_items


    def __register_game_items(self) -> None:
        invalid_items = {"fluid-unknown"} | {f"parameter-{i}" for i in range(10)}

        with self.modpack.open_file("Extractor/fluids.json") as file:
            fluids: set[str] = set(json.load(file))

        for fluid in fluids:
            ingredient = ItemNode(f"item_{fluid}")
            info: FactorioItemComponent = ingredient.register_component(FactorioItemComponent)
            info.is_fluid = True
            self.recipe_engine.add_node(ingredient)
            if fluid in invalid_items:
                ingredient.add_required(self.impossible_node, 1)

        with self.modpack.open_file("Extractor/items.json") as file:
            item_stack_sizes: dict[str, int] = json.load(file)

        for item, stack_size in item_stack_sizes.items():
            ingredient = ItemNode(f"item_{item}")
            info: FactorioItemComponent = ingredient.register_component(FactorioItemComponent)
            info.item_stack_size = stack_size
            self.recipe_engine.add_node(ingredient)
            if ingredient.name in self.modpack.ordered_science_packs or ingredient.name in invalid_items:
                ingredient.add_required(self.impossible_node, 1)

    def __register_categories(self) -> None:
        def get_or_create_category(name: str) -> CategoryNode:
            if f"category_{name}" not in self.recipe_engine.nodes:
                return self.recipe_engine.add_node(CategoryNode(f"category_{name}"))
            else:
                return self.get_single_category_node(name)

        with self.modpack.open_file("Extractor/machines.json") as file:
            raw_machines = json.load(file)

        for entity, categories in raw_machines.items():
            if entity == "character":
                for category in categories:
                    get_or_create_category(category).add_required(self.character_node, 0)
                    get_or_create_category(category).manual = True
                get_or_create_category("basic-crafting").add_required(self.character_node, 0) # somehow this is implied and not exported
                get_or_create_category("basic-solid").add_required(self.character_node, 0) # this is not a crafting category so not extracted todo look if some ores can't do this
                continue

            item = self.get_item_from_entity(entity)
            placed_entity = self.recipe_engine.add_node(PlacedEntityNode(f"placed_entity_{entity}"))
            placed_entity.add_required(item, 0)

            if item.name == "assembling-machine-1":
                get_or_create_category("crafting-with-fluid").add_required(placed_entity, 0) # mod enables this todo: disable?
            for category in categories:
                get_or_create_category(category).add_required(placed_entity, 0)

    def __register_recipes(self):
        with self.modpack.open_file("Extractor/resources.json") as file:  # todo find better method then opening twice
            raw_resources = json.load(file)

        for resource_name, resource_data in raw_resources.items():
            recipe = self.recipe_engine.add_node(RecipeNode(resource_name))
            recipe.cost = resource_data["mining_time"]

            for product, amount in resource_data["products"].items():
                recipe.add_used_by(self.get_item_node(product), amount)

            recipe.add_required(self.get_single_category_node(resource_data["category"]), 0)
            if "required_fluid" in resource_data:
                recipe.add_required(self.get_item_node(resource_data["required_fluid"]), resource_data["fluid_amount"])
                if resource_data["category"] == "basic-solid":
                    self.fluid_mining.add(recipe)
        del raw_resources

        with self.modpack.open_file("Extractor/recipes.json") as file:
            raw_recipes = json.load(file)

        for recipe_name, recipe_data in raw_recipes.items():
            # example "wheat-seeds":{"ingredients":{"wood":100},"products":{"wheat-seeds":1},"category":"organic-synth-recipes","energy":30}
            recipe = self.recipe_engine.add_node(RecipeNode(f"recipe_{recipe_name}"))

            recipe.cost = recipe_data["energy"]

            recipe.add_required(self.get_single_category_node(recipe_data["category"]), 0)
            for ingredient, amount in recipe_data["ingredients"].items():
                recipe.add_required(self.get_item_node(ingredient, strict=False), amount)

            for product, amount in recipe_data["products"].items():
                recipe.add_used_by(self.get_item_node(product, strict=False), amount)
        del raw_recipes

        with self.modpack.open_file("Extractor/generators.json") as file:
            raw_generators = json.load(file)
        for entity, product in raw_generators.items():
            item = self.get_item_from_entity(entity)
            recipe = self.recipe_engine.add_node(RecipeNode(f"generator_{item.name}"))
            recipe.cost = GENERATOR_ENERGY

            recipe.add_required(item, 0)

            recipe.add_used_by(self.get_item_node(product), 1)
        del raw_generators

        if "category_offshore-pump" in self.recipe_engine.nodes:
            fluids = set()
            with self.modpack.open_file("Extractor/specialTiles.json") as file:
                raw_tiles = json.load(file)
            for tile, special in raw_tiles.items():
                if "fluid" in special:
                    fluids.add(special["fluid"])
            del raw_tiles
            for fluid in fluids:
                recipe = self.recipe_engine.add_node(RecipeNode(f"pump_{fluid}"))
                recipe.cost = GENERATOR_ENERGY

                recipe.add_required(self.get_single_category_node("offshore-pump"),0)
                recipe.add_used_by(self.get_item_node(fluid), 1)

        try:
            with self.modpack.open_file("customRecipes.json") as file:
                raw_custom = json.load(file)
        except FileNotFoundError:
            raw_custom = {}

        for recipe_name, recipe_data in raw_custom.items():
            # TODO add optional crafting_machine_tints
            # TODO add group for AP recipes
            # TODO add support for custom techs for recipes
            recipe = self.recipe_engine.add_node(RecipeNode(recipe_name))

            recipe.cost = recipe_data["energy"]

            recipe.add_required(self.get_single_category_node(recipe_data["category"]), 0)
            for ingredient, amount in recipe_data["ingredients"].items():
                recipe.add_required(self.get_item_node(ingredient), amount)

            for product, amount in recipe_data["products"].items():
                recipe.add_used_by(self.get_item_node(product), amount)

    def __link_technologies(self):
        def add_technology(unlock: Node, tech: TechnologyNode):
            for node in unlock.required:
                if isinstance(node, MultiTechnologyNode):
                    node.add_required(tech, 0)
                    return
                elif isinstance(node, TechnologyNode):
                    unlock.remove_required({node}) # todo more efficient (post efficency pass on whole graph?)

                    multiTech = self.recipe_engine.add_node(MultiTechnologyNode(f"unlock_{unlock.name}"))
                    unlock.add_required(multiTech, 0)

                    multiTech.add_required(node, 0)
                    multiTech.add_required(tech, 0)
                    return

            unlock.add_required(tech, 0)

        for technology in self.modpack.base_technology_table.values():
            if not technology.unlocks and "mining-with-fluid" not in technology.modifiers:
                continue
            technology_node = self.recipe_engine.add_node(TechnologyNode(f"technology_{technology.name}"))
            self.technology_nodes[technology.name] = technology_node
            if "mining-with-fluid" in technology.modifiers:
                for recipe in self.fluid_mining:
                    recipe.add_required(technology_node, 0)

            for recipe_name in technology.unlocks:
                add_technology(self.recipe_engine.nodes[f"recipe_{recipe_name}"], technology_node)

    def __load_settings(self) -> None:
        with self.modpack.open_file("recipeEngineSettings.json") as file:
            raw_settings = json.load(file)

        if "missed_machines" in raw_settings:
            for name, categories in raw_settings["missed_machines"].items():
                item = self.get_item_from_entity(name)
                for category in categories:
                    self.recipe_engine.nodes[f"category_{name}"].add_required(item, 0)
            del raw_settings["missed_machines"]

        if "invalid_ingredients" in raw_settings:
            for ingredient in raw_settings["invalid_ingredients"]:
                self.get_item_node(ingredient).remove_required()
            del raw_settings["invalid_ingredients"]

        if "excluded_first_pool" in raw_settings:
            for ingredient in raw_settings["excluded_first_pool"]:
                component: FactorioItemComponent = self.get_item_node(ingredient).get_component(FactorioItemComponent)
                component.invalid_for_first_recipe_pool = True
            del raw_settings["excluded_first_pool"]

        for key in raw_settings.keys():
            self.modpack.logger.error(f"Unknown key in recipeEngineSettings.json: {key}")

    def get_item_from_entity(self, entity: str) -> ItemNode:
        if self.__dif_entity_to_item is None:
            with self.modpack.open_file("Extractor/entityToItem.json") as file:
                self.__dif_entity_to_item = json.load(file)

        if entity in self.__dif_entity_to_item:
            entity = self.__dif_entity_to_item[entity]

        return self.get_item_node(entity)

    def get_item_node(self, item: str, strict=True) -> ItemNode:
        if not strict and f"item_{item}" not in self.recipe_engine.nodes:
            # todo remove this
            # I would prefer all items to be found at item creation step
            # I do not know currently where rocket parts come or go though
            node = self.recipe_engine.add_node(ItemNode(f"item_{item}"))
            assert type(node) is ItemNode
            node: ItemNode
            node.register_component(FactorioItemComponent)
            return node
        node: Node = self.recipe_engine.nodes[f"item_{item}"]
        assert isinstance(node, ItemNode)
        node: ItemNode
        return node

    def get_recipe_node(self, recipe: str) -> RecipeNode:
        node: Node = self.recipe_engine.nodes[f"recipe_{recipe}"]
        assert isinstance(node, RecipeNode)
        node: ItemNode
        return node

    def get_single_category_node(self, category: str) -> CategoryNode:
        category: Node = self.recipe_engine.nodes[f"category_{category}"]
        assert isinstance(category, CategoryNode)
        category: CategoryNode
        return category

class CategoryNode(OrNode):
    pass

class TechnologyNode(OrNode):
    pass

class MultiTechnologyNode(OrNode):
    pass

class PlacedEntityNode(AndNode):
    def register_component(self, component_class: type[T]) -> T:
        component = super().register_component(component_class)
        if component_class is MultiLogicComponent:
            component: MultiLogicComponent
            component.promotion_node = True
        return component


class FactorioItemComponent(BaseNodeComponent):
    def __init__(self, owner: Node):
        super().__init__(owner)
        self.is_fluid = False
        self.item_stack_size: None | int = None

        self.invalid_for_first_recipe_pool = False
