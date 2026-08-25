local general = require("Archipelago/general")
require("Archipelago/locations")
require("Archipelago/custom_recipes")
local final_lib = require('libs/final-fixes')

data.raw["item"]["rocket-part"].hidden = false
data.raw["rocket-silo"]["rocket-silo"].fluid_boxes = {
    {
        production_type = "input",
        pipe_picture = assembler2pipepictures(),
        pipe_covers = pipecoverspictures(),
        volume = 1000,
        base_area = 10,
        base_level = -1,
        pipe_connections = {
            { flow_direction = "input", direction = defines.direction.south, position = { 0, 4.2 } },
            { flow_direction = "input", direction = defines.direction.north, position = { 0, -4.2 } },
            { flow_direction = "input", direction = defines.direction.east, position = { 4.2, 0 } },
            { flow_direction = "input", direction = defines.direction.west, position = { -4.2, 0 } }
        }
    },
    {
        production_type = "input",
        pipe_picture = assembler2pipepictures(),
        pipe_covers = pipecoverspictures(),
        volume = 1000,
        base_area = 10,
        base_level = -1,
        pipe_connections = {
            { flow_direction = "input", direction = defines.direction.south, position = { -3, 4.2 } },
            { flow_direction = "input", direction = defines.direction.north, position = { -3, -4.2 } },
            { flow_direction = "input", direction = defines.direction.east, position = { 4.2, -3 } },
            { flow_direction = "input", direction = defines.direction.west, position = { -4.2, -3 } }
        }
    },
    {
        production_type = "input",
        pipe_picture = assembler2pipepictures(),
        pipe_covers = pipecoverspictures(),
        volume = 1000,
        base_area = 10,
        base_level = -1,
        pipe_connections = {
            { flow_direction = "input", direction = defines.direction.south, position = { 3, 4.2 } },
            { flow_direction = "input", direction = defines.direction.north, position = { 3, -4.2 } },
            { flow_direction = "input", direction = defines.direction.east, position = { 4.2, 3 } },
            { flow_direction = "input", direction = defines.direction.west, position = { -4.2, 3 } }
        }
    }
}
data.raw["rocket-silo"]["rocket-silo"].fluid_boxes_off_when_no_fluid_recipe = true

if general.silo == 2 then
    data.raw["recipe"]["rocket-silo"].enabled = true
    technologies["rocket-silo"].enabled = false
    technologies["rocket-silo"].visible_when_disabled = false
end

data.raw["ammo"]["artillery-shell"].stack_size = 10

-- I am thinking that we might need to replace this entire function with one that will do all of this for ALL assembling machines that get made in any step of the process.
data.raw["assembling-machine"]["assembling-machine-1"].crafting_categories = table.deepcopy(data.raw["assembling-machine"]["assembling-machine-3"].crafting_categories)
data.raw["assembling-machine"]["assembling-machine-2"].crafting_categories = table.deepcopy(data.raw["assembling-machine"]["assembling-machine-3"].crafting_categories)
data.raw["assembling-machine"]["assembling-machine-1"].fluid_boxes = table.deepcopy(data.raw["assembling-machine"]["assembling-machine-2"].fluid_boxes)
if mods["factory-levels"] then
    -- Factory-Levels allows the assembling machines to get faster (and depending on settings), more productive at crafting products, the more the
    -- assembling machine crafts the product.  If the machine crafts enough, it may auto-upgrade to the next tier.
    for i = 1, 25, 1 do
        data.raw["assembling-machine"]["assembling-machine-1-level-" .. i].crafting_categories = table.deepcopy(data.raw["assembling-machine"]["assembling-machine-3"].crafting_categories)
        data.raw["assembling-machine"]["assembling-machine-1-level-" .. i].fluid_boxes = table.deepcopy(data.raw["assembling-machine"]["assembling-machine-2"].fluid_boxes)
    end
    for i = 1, 50, 1 do
        data.raw["assembling-machine"]["assembling-machine-2-level-" .. i].crafting_categories = table.deepcopy(data.raw["assembling-machine"]["assembling-machine-3"].crafting_categories)
    end
end

-- add all science packs to all labs
local known_packs = {}
for _, v in ipairs(general.science_packs.ordered) do
    known_packs[v] = true
end

for lab in pairs(data.raw["lab"]) do
    local science_packs = {}
    for i = 1, #general.science_packs.ordered do
        science_packs[i] = general.science_packs.ordered[i]
    end
    for i = 1, #data.raw["lab"][lab].inputs do
        if not known_packs[data.raw["lab"][lab].inputs[i]] then
            science_packs[i] = data.raw["lab"][lab].inputs[i]
        end
    end
    data.raw["lab"][lab].inputs = science_packs
end

function add_custom_tooltip_field(item, localised_name, localised_string, show_in_tooltip, order)
    if item.custom_tooltip_fields == nil then
        item.custom_tooltip_fields = { {
            name = localised_name,
            value = localised_string,
            show_in_tooltip = show_in_tooltip,
            order = order,
        } }
    else
        table.insert(item.custom_tooltip_fields, {
            name = localised_name,
            value = localised_string,
            show_in_tooltip = show_in_tooltip,
            order = order,
        })
    end
end

for _, name in pairs(general.recipes.enable_productivity()) do
    if data.raw["recipe"][name] == nil then
        error(name .." could not be found. This should be a recipe that is present at this point in the loading stage. This recipe is present in the list of recipes that get their productivity enabled.")
    end
    data.raw["recipe"][name].allow_productivity = true
end

-- Beserker note: This got complex, but seems to be required to hit all corner cases
local function adjust_energy(recipe_name, factor)
    local recipe = data.raw.recipe[recipe_name]
    if recipe == nil then return end

    local energy = recipe.energy_required

    if (recipe.normal ~= nil) then
        if (recipe.normal.energy_required == nil) then
            energy = 0.5
        else
            energy = recipe.normal.energy_required
        end
        recipe.normal.energy_required = energy * factor
    end
    if (recipe.expensive ~= nil) then
        if (recipe.expensive.energy_required == nil) then
            energy = 0.5
        else
            energy = recipe.expensive.energy_required
        end
        recipe.expensive.energy_required = energy * factor
    end
    if (energy ~= nil) then
        data.raw.recipe[recipe_name].energy_required = energy * factor
    elseif (recipe.expensive == nil and recipe.normal == nil) then
        data.raw.recipe[recipe_name].energy_required = 0.5 * factor
    end
end

local function set_energy(recipe_name, energy)
    local recipe = data.raw.recipe[recipe_name]
    if recipe == nil then return end

    if (recipe.normal ~= nil) then
        recipe.normal.energy_required = energy
    end
    if (recipe.expensive ~= nil) then
        recipe.expensive.energy_required = energy
    end
    if (recipe.expensive == nil and recipe.normal == nil) then
        recipe.energy_required = energy
    end
end

if general.recipes.type == "scale" then
    for name, adjustment in pairs(general.recipes.time_adjustments()) do
        adjust_energy(name, adjustment)
    end
end
if general.recipes.type == "range" then
    for name, adjustment in pairs(general.recipes.time_adjustments()) do
        set_energy(name, adjustment)
    end
end

local technologies = data.raw["technology"]

local stack_position = {}
local technology_name_to_progressive_group_name = {}
for progressive_name, progressive_group in pairs(general.technologies.progressive()) do
    local counter = 1
    for _, item in pairs(progressive_group) do
        technology_name_to_progressive_group_name[item] = progressive_name
        if stack_position[item] == nil then --ensure only the first instance of this item is found.
            stack_position[item] = counter
        end
        counter = counter + 1
    end
end

local setting = settings.startup["archipelago-show-techs-in-tech-screen"].value
for _, name in pairs(general.technologies.hide_from_player()) do
    if technologies[name] == nil then
        error(name .." could not be found. This should be a technology that is present at this point in the loading stage. This is present in the list of technologies that need to be hidden from the player, but not in the game.")
    end
    local tech = technologies[name]
    tech.archipelago_controlled = true
    tech.unit = nil

    if setting == "tech-tree" then
        tech.prerequisites = tech.prerequisites or {}
        table.insert(tech.prerequisites, "AP-lock")
    else
        tech.prerequisites = {"AP-lock"}
    end
    tech.research_trigger = {
        type = "scripted",
        icons = {final_lib.get_icon_from_type("advancement")}
    }

    if setting == "hidden" then
        tech.hidden = true
    end
    tech.hidden_in_factoriopedia = false  --does not have any effect weirdly enough.

    local stack_name = technology_name_to_progressive_group_name[name]
    if stack_name ~= nil then
        tech.research_trigger.trigger_description = {"archipelago.progressive-script-trigger", stack_position[name].."", stack_name}
        --yes, adding that empty string is important.
        if stack_position[name] < 10 then
            tech.order = "zz-ap-"..stack_name.."-00"..stack_position[name]
        elseif stack_position[name] < 100 then
            tech.order = "zz-ap-"..stack_name.."-0"..stack_position[name]
        else
            tech.order = "zz-ap-"..stack_name.."-"..stack_position[name]
        end
    else
        tech.research_trigger.trigger_description = {"archipelago.stand-alone-script-trigger", name}
        tech.order = "zz-ap-"..name
    end
end

local researched_techs = {}
researched_techs["Starting-recipes"] = true
for _, name in pairs(general.technologies.removed_technologies()) do
    local tech = technologies[name]
    tech.order = "za-ap-unlocked"
    tech.research_trigger.trigger_description = {"archipelago.default-unlocked-script-trigger"}
    tech.research_trigger.icons = {final_lib.get_icon_from_type("unlocked")}
    researched_techs[name] = true
end

for tech_name, tech in pairs(technologies) do
    if not researched_techs[tech_name] and tech.effects then
        local temp_tech_localisation
        if string.find(tech_name, "-%d$") then
            local pure_tech_name = string.gsub(tech_name, "-%d$", "")
            local tech_number = string.gsub(tech_name, "^.+-", "")
            temp_tech_localisation = {"", {"technology-name."..pure_tech_name}, " "..tech_number}
        end
        for _, effect in pairs(tech.effects) do
            local tech_localised = tech.localised_name or temp_tech_localisation or  {"technology-name."..tech_name}
            if effect.type == "unlock-recipe" then
                local recipe = data.raw.recipe[effect.recipe]
                local order = recipe.custom_tool_tip_order or 40
                add_custom_tooltip_field(recipe, {"factoriopedia.recipe-unlock"}, tech_localised, false, order)
                if tech.archipelago_controlled then
                    add_custom_tooltip_field(recipe, {"factoriopedia.ap-unlock"}, tech.research_trigger.trigger_description, false, order+1)
                end
                recipe.custom_tool_tip_order = order + 2
            end
        end
    end
end