#convert raw data json into item list and recipie list

#store nicely in python. Could output to csv but not right now
#maybe we'll output to csv for use by ML models
#chosen data structure
#   items[{name:, type:, fuel_value:, fuel_category:}]
#   recipes[{name:, type:, category:, seconds:, ingredients:, results:}]
#       ingredients[{name:, amount:}]
#       results[{name:, amont:}]
#alternate data structures
#   table objects
#   ingredients[{item:qty, item:qty}]
#   libraries of objects
#   items{separate item names:{}} - nice for finding them, easy to switch

itemPath = "C:\\Users\\natha\\Desktop\\Factorio\\luaData\\item - trimmed.lua"
technologyPath = "C:\\Users\\natha\\Desktop\\Factorio\\luaData\\technology - trimmed.lua"
recipePath = "C:\\Users\\natha\\Desktop\\Factorio\\luaData\\recipe - trimmed.lua"


import slpp
from slpp import slpp
import sys

class trashCode(object):
    def failedJsonParsing():
        print("hey")

        #https://stackoverflow.com/questions/10382253/reading-rather-large-json-files

        #import bigjson
        #import jsonstreamer
        #import pandas as pd
        #import json

        # myarray = json.loads("C:\\Users\\natha\\Desktop\\Factorio\\raw_data.txt") #doesn't work this way

        # df = pd.read_json("C:\\Users\\natha\\Desktop\\Factorio\\raw_data.txt", lines=True) #doesn't work this way

        # with open("C:\\Users\\natha\\Desktop\\Factorio\\raw_data.txt") as f:
        #     myvar = json.load(f)
        #     print(myvar) #cuts it off after a certain number of characters

        # with open("C:\\Users\\natha\\Desktop\\Factorio\\raw_data.txt", 'rb') as f:
        #     myvar = bigjson.load(f) 
        #     print(type(myvar)) #is some kind of object
        #     print(len(myvar)) #19, correct. 19 top level json object things

        #     element = myvar["accumulator"]["accumulator"]["energy_source"]
        #     print(type(element)) #object
        #     print(element)
        #     print(len(element))

        #     # for x in element:
        #     #     print(x)
        #     print(element[0])
        #     print(element[1])

        #     element = myvar["accumulator"]["accumulator"]["energy_source"]["buffer_capacity"]
        #     print(type(element)) #string
        #     print(element)
        #     print(len(element))

        #     for x in myvar: #error key must be a string
        #         print(x)

        #     element = myvar['type']
        #     element = myvar[0]
        #     print(element['type'])
        #     print(element['id'])
        #     for athing in myvar:
        #       print(athing)



        # with open("C:\\Users\\natha\\Desktop\\Factorio\\raw_data.txt") as f:
        #     myvar = ijson.items(f, "recipes.item")
        #     print(myvar)
        #     for i in myvar:
        #         print(i)

    def failedLuaParsing():
        print("hey")
        # from luaparser import ast
        # from luaparser import astnodes
        # tree = ast.parse(open("C:\\Users\\natha\\Desktop\\Factorio\\item.lua"))
        # for node in ast.walk(tree):
        #     print(node)
        #     if isinstance(node, astnodes.Name):
        #         print(node)

    #using ijson
    def jsonItem(): #loads in the json or lua and creates csv and internal use array
        print("hey")
        # import ijson

        # #--------items json------------#
        # f = open("C:\\Users\\natha\\Desktop\\Factorio\\items.txt", 'w') #might use csv extension later. Using txt for easy open right now

        # f.write("group,localized_name,name,order,stack_size,subgroup,type\n") #I think \r is CR and \n is cr lf
        # # parser = ijson.parse(open("C:\\Users\\natha\\Desktop\\Factorio\\raw_data.txt"))
        # parser = ijson.parse(open("C:\\Users\\natha\\Desktop\\Factorio\\item - trimmed.lua"))
        # item_name = ""
        # items = [] #could use set...maybe?, but then can't iterate over it as easy, or maybe get random order in an "for in" statement, but worst can't even check inside as easy
        # for prefix, event, value in parser:
        #     # print(prefix, event, value)
        #     if prefix == "items" and event == "map_key": #beginning of an item
        #         # print(value) #name of item
        #         item_name = value
        #         newItem = item()
        #     if prefix == "items." + item_name + ".group":
        #         f.write(value)
        #         newItem.group = value
        #     if prefix == "items." + item_name + ".localized_name.en":
        #         f.write("," + value)
        #         newItem.localized_name = value
        #     if prefix == "items." + item_name + ".name":
        #         f.write("," + value)
        #         newItem.name = value
        #     if prefix == "items." + item_name + ".order":
        #         f.write("," + value)
        #         newItem.order = value
        #     if prefix == "items." + item_name + ".stack_size":
        #         f.write("," + str(value))
        #         newItem.stack_size = value
        #     if prefix == "items." + item_name + ".subgroup":
        #         f.write("," + value)
        #         newItem.subgroup = value
        #     if prefix == "items." + item_name + ".type":
        #         f.write("," + value)
        #         newItem.type = value
        #     if prefix == "items." + item_name and event == "end_map":
        #         f.write("\n") 
        #         items.append(newItem)
        # f.close()  

class dataParse(object):

    def __init__(self, itemPath, technologyPath, recipePath):
        self.loadItems = [] #will be a list of dictionaries
        self.loadRecipes = []
        self.loadTechnology = []
        self.items = {} #will this make a dictionary?
        self.recipes = {}

        print(type(self.items))

        self.luaItem(itemPath)
        self.luaTechnology(technologyPath)
        self.luaRecipe(recipePath)
        self.synthesizeItems()
        self.synthesizeRecipes()
        self.validation()

    def codePlan():
        print("hey")
        #check categories and edge cases
            #infinite tech
            #not allowed items, categories
            #fluids, steam, water
            #electricity as item or separate or whatever
            #rocket craft from rocket parts
            #hand crafting
            #human as an item
            #human mining as recipes
        
            #adds items
            #   tech (reg and incremental)
            #   engineer
            #   fluids (in separate file we won't ingest) - oil, heavy, light, petrol, water, steam, ignore heat
            #   electricity (needs special handling, measured in power? or joules and removed every time unit?)
            #adds to existing recipies
            #   final techs (qty0), including dummy steel axe output 
            #   assemblers (assemblers 1-3, refinery, chemical, human, solar panel, steam engine, forget about uranium maybe) to recipies
            #   energy consumption
            #   optional inserters, belts
            #add more recipies
            #   incremental tech
            #   final techs from incremental tech
            #   power consumption
            #   power generation
            #   human mining, plus ones including dummy steel axe
            #   creating the rocket (include variant with satellite, outputting space science)

            #CONCESSIONS
            #no uranium stuff
            #only use coal to fuel steam generators, furnaces, etc (not including wood)
            #no wood cutting recipe
            #machines can only operate at full power
            #not doing barrels right now
            #no accumulators in their normal way
            #solar panels output continuously (averaged day/night output 42kw) and require 0.84 of an accumulator to deliver power
            #no potential boosts to crafting speeds from technology (lab research speed is the only one, I guess)
            #no modules or beacons

            #FUNNY stuff with machines take longer than 1/60 to craft, but we produce energy continuously. Will have to make gameplay logic interesting for energy consumption of ongoing crafts

            #item properties we care about
            #   name
            #   display name (can be found in en config file, forget about it)
            #   fuel_value
            #   fuel_category (chemical, nuclear, nathan adds none)
            #   type (in case we need to outlaw stuff)

            #recipe properties we care about
            #   type (all recipe?)
            #   name
            #   category (null=crafting?, crafting, basic-crafting, advanced-crafting, smelting, chemistry, crafting-with-fluid, oil-processing, rocket-building, centrifuging, nathan adds steam, power)
            #   enabled t/f & not present. Defaults to true??? 
            #       enabled=iron-chest,light-armor,stone-brick
            #       missing matches starting available except enabled=True and also includes: submachine gun, assembling-machine-2, steel-plate, cannon shell, explosive cannon shell, express transport belt, tank, advanced circuit, processing unit, explosives, battery, low density structure
            #       but there is tech to unlock lds but not iron-chest...
            #   ingredients [{type, name, amount}] OR [[item, qty]]
            #   energy_required = time (at craft speed 1)
            #   result [[item, qty]] OR [{}] OR {}

            #tech properties we care about
            #   type (all are technology)
            #   name
            #   prerequisites (is a list)
            #   effects (list of dictionaries)
            #       'type':'unlock-recipe'
            #       'recipe': nameofrecipe
            #   unit (dictionary)
            #       'count' * strip(1)
            #       ingredients[[]], inner list is just [item, qty] OR set of set
            #       time

    def rawDataExamples():
        print("hey")
        #eg_lua_data = '{{type = "item",name = "stone-brick",place_as_tile = {result = "stone-path",condition_size = 1,condition = { "water-tile" }}},{type = "item",name = "wood"}}'
        #json items
            # "advanced-circuit": {
            #     "group": "intermediate-products",
            #     "icon_col": 1,
            #     "icon_row": 0,
            #     "localized_name": {
            #         "en": "Advanced circuit"
            #     },
            #     "name": "advanced-circuit",
            #     "order": "f[advanced-circuit]",
            #     "stack_size": 200,
            #     "subgroup": "intermediate-product",
            #     "type": "item"
            # },
        #lua item
            # {
            #     type = "item",
            #     name = "wood",
            #     icon = "__base__/graphics/icons/wood.png",
            #     icon_size = 64, icon_mipmaps = 4,
            #     fuel_value = "2MJ",
            #     fuel_category = "chemical",
            #     subgroup = "raw-resource",
            #     order = "a[wood]",
            #     stack_size = 100
            # }
        #json recipe data structure
            # "advanced-oil-processing": {
            #     "category": "oil-processing",
            #     "enabled": false,
            #     "energy_required": 5,
            #     "icon_col": 2,
            #     "icon_mipmaps": 4,
            #     "icon_row": 0,
            #     "icon_size": 64,
            #     "ingredients": [ {
            #         "amount": 50,
            #         "name": "water",
            #         "type": "fluid"
            #     }, {
            #         "amount": 100,
            #         "name": "crude-oil",
            #         "type": "fluid"
            #     } ],
            #     "localized_name": {
            #         "en": "Advanced oil processing"
            #     },
            #     "name": "advanced-oil-processing",
            #     "order": "a[oil-processing]-b[advanced-oil-processing]",
            #     "results": [ {
            #         "amount": 25,
            #         "name": "heavy-oil",
            #         "type": "fluid"
            #     }, {
            #         "amount": 45,
            #         "name": "light-oil",
            #         "type": "fluid"
            #     }, {
            #         "amount": 55,
            #         "name": "petroleum-gas",
            #         "type": "fluid"
            #     } ],
            #     "subgroup": "fluid-recipes",
            #     "type": "recipe"
            # },
        #lua tech
            # {
            #     type = "technology",
            #     name = "stronger-explosives-1",
            #     icon_size = 256, icon_mipmaps = 4,
            #     icons = util.technology_icon_constant_damage(stronger_explosives_1_icon),
            #     effects =
            #     {
            #     {
            #         type = "ammo-damage",
            #         ammo_category = "grenade",
            #         modifier = 0.25
            #     }
            #     },
            #     prerequisites = {"military-2"},
            #     unit =
            #     {
            #     count = 100*1,
            #     ingredients =
            #     {
            #         {"automation-science-pack", 1},
            #         {"logistic-science-pack", 1}
            #     },
            #     time = 30
            #     },
            #     upgrade = true,
            #     order = "e-j-a"
            # }

    def throwError(self, data, errorDescription):
        print(data)
        print(errorDescription)
        sys.exit()

    def luaItem(self, itemPath): #is a list of dictionaries.
        #just removed some front matter and end parenthese
        data = slpp.decode(open(itemPath).read())
        self.loadItems = data[:]
        #TYPES
        # itemTypes = set()
        # for x in data:
        #     if x["type"] not in itemTypes:
        #         itemTypes.add(x["type"])
        # print(itemTypes)
        # most things: 'item'
        # debug/ignore: 'item-with-label', 'blueprint', 'copy-paste-tool', 'upgrade-item', 'spidertron-remote', 'blueprint-book', 'item-with-tags', 'item-with-inventory', 'deconstruction-item', 'selection-tool'
        # normal but looks funny: 'capsule' (includes grenade), 'tool' (all the science packs), 'mining-tool' (we'll make the dummy-steel-axe an output to final tech used in personal mining recipes), 'item-with-entity-data' (cars, trains, etc)
        # very normal, not neccessarily used in optimization: 'module', 'ammo' (includes 'rocket' which is an rpg), 'repair-tool', 'armor', 'rail-planner' (just rail item), 'gun'
        # I added: fluid, engineer
        # for x in data:
        #     if x["type"] == 'selection-tool':
        #         print(x["name"])

    def luaTechnology(self, technologyPath):
        #has the wrappers removed, blocks combined, and infinite tech removed
        data = slpp.decode(open(technologyPath).read())
        self.loadTechnology = data[:]

        #TYPES
        for x in data:
            if x["type"] != "technology":
                self.throwError(x, "tech that is not type=technology") #all types are technology
    
    def luaRecipe(self, recipePath):
        #has the wrappers removed, blocks combined, and infinite tech removed
        data = slpp.decode(open(recipePath).read())
        self.loadRecipes = data[:]

        #TYPES
        for x in data:
            if x["type"] != "recipe":
                self.throwError(x, "recipe that is not type=recipe") #all types are recipe
        #ENABLED
        # for x in data:
        #     if "enabled" in x:
        #         if x["enabled"] == True:
        #             print("enabled:", x["name"])
        #     else:
        #         print("no enabled field:", x["name"])
        #CATEGORY
        # recCats = set()
        # for x in data:
        #     if "category" in x:
        #         if x["category"] not in recCats:
        #             recCats.add(x["category"])
        # print(recCats)
        # normal stuff: 'oil-processing', 'chemistry', 'smelting', 'crafting-with-fluid' (normal assemblers using fluid, add steam stuff in here)
        # special stuff: 'centrifuging' (4 things related to uranium, not handled yet), 'rocket-building' (rocket part only, I added launching), 
        # don't understand: 'advanced-crafting' (engine unit), 'crafting' (empty barrel, hazard concrete, refined concrete, landfill, low density, rcu, satellite) 
        # nathan added: 'none' (not provided in data), 'power', 'mining' (then expanded)
        # for x in data:
        #     if "category" in x:
        #         if x["category"] == 'crafting-with-fluid':
        #             print(x["name"])

    def handleLists(self, loadDict, recipe, readList, loadList):
        if readList not in ["ingredients", "results", "prerequisites"]:
            self.throwError(readList, "handeLists exception type")
        
        if loadList not in loadDict: #idk if needs initialization
            loadDict[loadList] = []

        #deal with normal vs expensive and result vs results
        if "normal" in recipe:
            loadArray = recipe["normal"]
        elif readList == "ingredients" and "unit" in recipe: #for tech
            loadArray = recipe["unit"]
        else:
            loadArray = recipe
        #deal with result count (should always coincide with singular result, but whatever. Idk if in normal or outside, so less risk here)
        if "result_count" in recipe:
            separateCount = recipe["result_count"]
        elif "result_count" in loadArray:
            separateCount = loadArray["result_count"]
        elif readList == "prerequisites":
            separateCount = 0
        else:
            separateCount = 1
        #deal with result vs results
        if readList in loadArray:
            loadArray = loadArray[readList] #idk why this doesn't have copy issues
        elif readList == "results" and "result" in loadArray:
            loadArray = loadArray["result"]
        else:
            self.throwError(loadArray, "self.handleLists readList " + readList + " not in loadArray")
        #tech units
        if readList == "prerequisites":
            suffix = "-technology-full"
        else:
            suffix = ""

        #actually load in ingredients or results
        if type(loadArray) == dict: #Only one ingredient. This never happens with results. 
            if len(loadArray) != 1:
                self.throwError(loadArray, "loadArray, is dict of lenth <> 1")
            loadDict[loadList].append(loadArray)
        elif type(loadArray) == list:
            for y in loadArray:
                if type(y) == list: #typically of form [[item, qty]]
                    if len(y) != 2:
                        self.throwError(recipe, "recipe unexpected data type")
                    loadDict[loadList].append({"name":y[0]+suffix, "amount":y[1]})
                elif type(y) == dict: #good form [{name:item, amount:qty}]
                    loadDict[loadList].append({"name":y["name"]+suffix, "amount":y["amount"]})
                    #type, name, amount, fluidbox_index = 2, 3
                elif type(y) == str: #occurs in tech prereqs
                    loadDict[loadList].append({"name":y+suffix, "amount":separateCount})
                else:
                    self.throwError(recipe, "recipe unexpected data type")
        elif type(loadArray) == str: #this never happens with ingredients
            loadDict[loadList].append({"name":loadArray+suffix, "amount":separateCount})
        else:
            self.throwError(recipe, "recipe unexpected data type")
        
        return loadDict

    def synthesizeItems(self):

        #ITEMS
        #do we even want to do fuel value stuff?

        self.items.append({"name":"engineer", "type":"engineer", "fuel_value":0, "fuel_category":"none"})
        #fluids, won't bother getting them from separate file
        self.items.append({"name":"water", "type":"fluid", "fuel_value":0, "fuel_category":"none"})
        self.items.append({"name":"steam", "type":"fluid", "fuel_value":0, "fuel_category":"none"})
        self.items.append({"name":"sulfuric-acid", "type":"fluid", "fuel_value":0, "fuel_category":"none"})
        self.items.append({"name":"crude-oil", "type":"fluid", "fuel_value":0, "fuel_category":"none"})
        self.items.append({"name":"heavy-oil", "type":"fluid", "fuel_value":0, "fuel_category":"none"})
        self.items.append({"name":"light-oil", "type":"fluid", "fuel_value":0, "fuel_category":"none"}) 
        self.items.append({"name":"petroleum-gas", "type":"fluid", "fuel_value":0, "fuel_category":"none"}) 
        self.items.append({"name":"lubricant", "type":"fluid", "fuel_value":0, "fuel_category":"none"})
        #electricity
        self.items.append({"name":"electricity", "type":"electricity", "fuel_value":0, "fuel_category":"none"})
        #normal items
        for x in self.loadItems:
            loadDict = {}
            loadDict["name"] = x["name"]
            loadDict["type"] = x["type"]
            if "fuel_value" in x:
                loadDict["fuel_value"] = x["fuel_value"]
                loadDict["fuel_category"] = x["fuel_category"]
            else:
                loadDict["fuel_value"] = 0
                loadDict["fuel_category"] = "none"
            self.items.append(loadDict)
        #technology (unit and full)
        for x in self.loadTechnology:
            loadDict = {}
            loadDict["name"] = x["name"] + "-technology-full"
            loadDict["type"] = x["type"] + "-full"
            loadDict["fuel_value"] = 0
            loadDict["fuel_category"] = "none"
            self.items.append(loadDict)
            loadDict = {}
            loadDict["name"] = x["name"] + "-technology-unit"
            loadDict["type"] = x["type"] + "-unit"
            loadDict["fuel_value"] = 0
            loadDict["fuel_category"] = "none"
            self.items.append(loadDict)
        
    def synthesizeRecipes(self):
        #RECIPES
        #odd recipies
        #mining (divide seconds by mining rate of machine to get actual seconds/item). We'll add energy and machines later
        self.recipes.append({"name":"mine-iron", "type":"recipe", "category":"mining", "seconds":1, "ingredients":[], "results":[{"name":"iron-ore", "amount":1}]})
        self.recipes.append({"name":"mine-copper", "type":"recipe", "category":"mining", "seconds":1, "ingredients":[], "results":[{"name":"copper-ore", "amount":1}]})
        self.recipes.append({"name":"mine-coal", "type":"recipe", "category":"mining", "seconds":1, "ingredients":[], "results":[{"name":"coal", "amount":1}]})
        self.recipes.append({"name":"mine-stone", "type":"recipe", "category":"mining", "seconds":1, "ingredients":[], "results":[{"name":"stone", "amount":1}]})
        self.recipes.append({"name":"mine-uranium", "type":"recipe", "category":"mining", "seconds":2, "ingredients":[], "results":[{"name":"uranium-ore", "amount":1}]})
        #pumpjack
        self.recipes.append({"name":"mine-oil", "type":"recipe", "category":"mining-special", "seconds":1, "ingredients":[{"name":"pumpjack","amount":1}], "results":[{"name":"pumpjack","amount":1},{"name":"crude-oil", "amount":2},{"name":"electricity","amount":90000}]}) #90kw
            #at full depletion, oil produces 2/sec
            #90kw
        #fish & wood
        self.recipes.append({"name":"mine-fish", "type":"recipe", "category":"mining-special", "seconds":1, "ingredients":[{"name":"engineer", "amount":1}], "results":[{"name":"engineer","amount":1},{"name":"raw-fish", "amount":1}]})
        self.recipes.append({"name":"mine-wood", "type":"recipe", "category":"mining-special", "seconds":1, "ingredients":[{"name":"engineer", "amount":1}], "results":[{"name":"engineer","amount":1},{"name":"wood", "amount":1}]})
            #idk actual mechancis of fishing or wood chopping, might be affected by steel axe
            #can fish with robots?
        #energy stuff
        self.recipes.append({"name":"mine-water", "type":"recipe", "category":"power", "seconds":1/60, "ingredients":[{"name":"offshore-pump", "amount":1}], "results":[{"name":"water", "amount":20},{"name":"offshore-pump", "amount":1}]}) #offshore pump
        self.recipes.append({"name":"boil-water", "type":"recipe", "category":"power", "seconds":1/60, "ingredients":[{"name":"boiler", "amount":1},{"name":"water","amount":1},{"name":"coal","amount":0.0075}], "results":[{"name":"steam", "amount":1},{"name":"boiler", "amount":1}]}) #boiler
            #consume 1.8MW, coal is 4MJ so... consumes a little under 1/2sec
        self.recipes.append({"name":"steam-power", "type":"recipe", "category":"power", "seconds":1/60, "ingredients":[{"name":"steam-engine", "amount":1},{"name":"steam","amount":0.5}], "results":[{"name":"steam-engine", "amount":1},{"name":"electricity", "amount":15000}]})
            #900kw = 15000j every 1/60 of a second
        self.recipes.append({"name":"solar-power", "type":"recipe", "category":"power", "seconds":1/60, "ingredients":[{"name":"solar-panel", "amount":1},{"name":"accumulator","amount":0.84}], "results":[{"name":"solar-panel", "amount":1},{"name":"accumulator","amount":0.84},{"name":"electricity", "amount":700}]})
            #solar panel is average 42kw = 700j every 1/60 of second
            #requires 0.84 accumulators
            #each day is 25000 ticks, 416.666 seconds
            #one tick = 0.016666 seconds = 1/60th of a second
        self.recipes.append({"name":"launch-rocket", "type":"recipe", "category":"rocket-building", "seconds":30, "ingredients":[{"name":"rocket-part", "amount":100}], "results":[]})
        self.recipes.append({"name":"launch-rocket-with-satellite", "type":"recipe", "category":"rocket-building", "seconds":30, "ingredients":[{"name":"rocket-part", "amount":100},{"name":"satellite", "amount":1}], "results":[{"name":"space-science-pack", "amount":1000}]})
            #idk how long it actually takes. I timed it at 10 seconds to prepare and about 15 to launch fully, and 5 to be ready to build again
            #add item for winning the game?

        #regular recipes
        for recipe in self.loadRecipes:
            # if recipe["name"] == "speed-module":
            #     print("hey")

            loadDict = {}

            loadDict["name"] = recipe["name"]
            loadDict["type"] = recipe["type"] #these will be all 'recipe'

            if "category" in recipe:
                loadDict["category"] = recipe["category"] #helps with adding machines
            else:
                loadDict["category"] = "none"

            # loadDict["enabled"] = x["enabled"] #this is funky business. If something doesn't have a tech in the recipe, it can happend without enabling
            
            if "energy_required" in recipe: #for some reason, in the lua data, the time in seconds is listed as energy required
                    loadDict["seconds"] = recipe["energy_required"] 
            elif "normal" in recipe:
                if "energy_required" in recipe["normal"]:
                    loadDict["seconds"] = recipe["normal"]["energy_required"] 
            if "seconds" not in loadDict: #I checked via game, all not found are 0.5 seconds. And I think all 0.5 seconds are not found as well
                loadDict["seconds"] = 0.5
            
            loadDict = self.handleLists(loadDict, recipe, "ingredients", "ingredients")
            loadDict = self.handleLists(loadDict, recipe, "results", "results")

            self.recipes.append(loadDict)
            
        #add tech unit and full
        for recipe in self.loadTechnology:
            #add tech units
            loadDict = {}

            loadDict["name"] = recipe["name"] + "-technology-unit"
            loadDict["type"] = recipe["type"] #all these will be "technology"
            loadDict["category"] = "technology-unit"
            loadDict["seconds"] = recipe["unit"]["time"]

            loadDict = self.handleLists(loadDict, recipe, "ingredients", "ingredients")
            if "prerequisites" in recipe:
                loadDict = self.handleLists(loadDict, recipe, "prerequisites", "ingredients")
            loadDict["ingredients"].append({"name":"lab", "amount":1}) #lab is required to do this
            loadDict["results"] = []
            loadDict["results"].append({"name":"lab", "amount":1})
            loadDict["results"].append({"name":loadDict["name"], "amount":1}) #actually produce the tech unit

            self.recipes.append(loadDict)
        
            #add tech full tech
            loadDict = {}

            loadDict["name"] = recipe["name"] + "-technology-full"
            loadDict["type"] = recipe["type"] #all these will be "technology"
            loadDict["category"] = "technology-full"
            loadDict["seconds"] = 0

            #add itself as units as ingredients to full tech
            loadDict["ingredients"] = []
            if 1 in recipe["unit"]:
                amount = int(recipe["unit"][1].replace("*", ""))
            else:
                amount = 1
            loadDict["ingredients"].append({"name":recipe["name"] + "-technology-unit", "amount":recipe["unit"]["count"]*amount})
            loadDict["results"] = []
            loadDict["results"].append({"name":loadDict["name"], "amount":1})
            self.recipes.append(loadDict)
            
        #add tech full as 0 ingredient to recipies unlocked by them
        for recipe in self.loadTechnology:
            if "effects" in recipe:
                for effect in recipe["effects"]:
                    if effect["type"] == "unlock-recipe":
                        #find the recipe and add itself as 0 ingredient
                        for myrec in self.recipes:
                            if myrec["name"] == effect["recipe"]:
                                if myrec["type"] != "recipe":
                                    self.throwError(recipe, "found an unlock for a non-recipe")
                                myrec["ingredients"].append({"name":recipe["name"] + "-technology-full", "amount":0})
                                break

        
        #adding machine and energy cost to recipies, eng mining, mining, oil, chem, smelt, 1-3 craft, hand craft, fluids, rocket building
        addRecipes = []
        for recipe in self.recipes:
            if recipe["category"] == "mining":
                #engineer w/o axe
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"engineer", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/0.5
                tempRecipe["results"].append({"name":"engineer", "amount":1})
                addRecipes.append(tempRecipe)
                #engineer with axe
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"engineer", "amount":1})
                tempRecipe["ingredients"].append({"name":"steel-axe-technology-full", "amount":0})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/1
                tempRecipe["results"].append({"name":"engineer", "amount":1})
                addRecipes.append(tempRecipe)
                #burner
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"burner-mining-drill", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/0.25
                tempRecipe["ingredients"].append({"name":"coal", "amount":150000*tempRecipe["seconds"]/4000000}) #coal is 4mj, drill takes 150kw for 4 sec
                tempRecipe["results"].append({"name":"burner-mining-drill", "amount":1})
                addRecipes.append(tempRecipe)
                #electric
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"electric-mining-drill", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/0.5
                tempRecipe["ingredients"].append({"name":"electricity", "amount":90000*tempRecipe["seconds"]})
                tempRecipe["results"].append({"name":"electric-mining-drill", "amount":1})
                addRecipes.append(tempRecipe)
                #remove template
                self.recipes.remove(recipe)
            if recipe["category"] == "oil-processing":
                tempRecipe = recipe
                tempRecipe["ingredients"].append({"name":"oil-refinery", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])
                tempRecipe["ingredients"].append({"name":"electricity", "amount":434000*tempRecipe["seconds"]}) #434kw
                tempRecipe["results"].append({"name":"oil-refinery", "amount":1})
                addRecipes.append(tempRecipe)
                self.recipes.remove(recipe)
            if recipe["category"] == "chemistry":
                tempRecipe = recipe
                tempRecipe["ingredients"].append({"name":"chemical-plant", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])
                tempRecipe["ingredients"].append({"name":"electricity", "amount":217000*tempRecipe["seconds"]}) #217kw
                tempRecipe["results"].append({"name":"chemical-plant", "amount":1})
                addRecipes.append(tempRecipe)
                self.recipes.remove(recipe)
            if recipe["category"] == "smelting":
                #stone furnace
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"stone-furnace", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/1
                tempRecipe["ingredients"].append({"name":"coal", "amount":90000*tempRecipe["seconds"]/4000000}) #90kw, coal is 4mj
                tempRecipe["results"].append({"name":"stone-furnace", "amount":1})
                addRecipes.append(tempRecipe)
                #steel furnace
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"steel-furnace", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/2
                tempRecipe["ingredients"].append({"name":"coal", "amount":90000*tempRecipe["seconds"]/4000000}) #90kw, coal is 4mj
                tempRecipe["results"].append({"name":"steel-furnace", "amount":1})
                addRecipes.append(tempRecipe)
                #electric furnace
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"electric-furnace", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/2
                tempRecipe["ingredients"].append({"name":"electricity", "amount":186000*tempRecipe["seconds"]}) #186kw
                tempRecipe["results"].append({"name":"electric-furnace", "amount":1})
                addRecipes.append(tempRecipe)
                #remove template (Built-in)
                self.recipes.remove(recipe)
            if recipe["category"] in ["none", "crafting", "advanced-crafting", "crafting-with-fluids"]:
                if recipe["category"] != "crafting-with-fluids":
                    #engineer
                    tempRecipe = recipe.copy()
                    tempRecipe["ingredients"] = recipe["ingredients"].copy()
                    tempRecipe["results"] = recipe["results"].copy()
                        #fromKeys doesn't actually change tempRecipe
                        #copy() does the same as without copy, because it's shallow. The sublists (ingred and results) are same reference
                        # dict.items() is a set or something, can't be worked with
                    tempRecipe["ingredients"].append({"name":"engineer", "amount":1})
                    tempRecipe["seconds"] = float(tempRecipe["seconds"])/1
                    tempRecipe["results"].append({"name":"engineer", "amount":1})
                    addRecipes.append(tempRecipe)
                    #assy 1
                    tempRecipe = recipe.copy()
                    tempRecipe["ingredients"] = recipe["ingredients"].copy()
                    tempRecipe["results"] = recipe["results"].copy()
                    tempRecipe["ingredients"].append({"name":"assembling-machine-1", "amount":1})
                    tempRecipe["seconds"] = float(tempRecipe["seconds"])/0.5
                    tempRecipe["ingredients"].append({"name":"electricity", "amount":77500*tempRecipe["seconds"]}) #77.5kw
                    tempRecipe["results"].append({"name":"assembling-machine-1", "amount":1})
                    addRecipes.append(tempRecipe)
                #assy 2
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"assembling-machine-2", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/0.75
                tempRecipe["ingredients"].append({"name":"electricity", "amount":155000*tempRecipe["seconds"]}) #155kw
                tempRecipe["results"].append({"name":"assembling-machine-2", "amount":1})
                addRecipes.append(tempRecipe)
                #assy 3
                tempRecipe = recipe.copy()
                tempRecipe["ingredients"] = recipe["ingredients"].copy()
                tempRecipe["results"] = recipe["results"].copy()
                tempRecipe["ingredients"].append({"name":"assembling-machine-3", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/1.25
                tempRecipe["ingredients"].append({"name":"electricity", "amount":388000*tempRecipe["seconds"]}) #388kw
                tempRecipe["results"].append({"name":"assembling-machine-3", "amount":1})
                addRecipes.append(tempRecipe)
            if recipe["category"] == "rocket-building":
                tempRecipe = recipe
                tempRecipe["ingredients"].append({"name":"rocket-silo", "amount":1})
                tempRecipe["seconds"] = float(tempRecipe["seconds"])/1
                tempRecipe["ingredients"].append({"name":"electricity", "amount":4000000*tempRecipe["seconds"]}) #4mw
                tempRecipe["results"].append({"name":"rocket-silo", "amount":1})
        #add in the new recipes we created from the variations
        self.recipes.extend(addRecipes)


        #assemblers
        #   reg = 0.5, 77.5kw
        #   lvl2 = 0.75, liquids, 155kw
        #   lvl3 = 1.25, liquids, 388kw
        #   engineer = 1


        #problem with electricity storage... consuming the electricity at start of recipe... unless I go weird and consume it throughout...

    def validation(self):
        #check all amounts and seconds are floats/numbers, not strings
        #check all ingredients and results are in the items list
        #check for orphans?

        #item columns
        for item in self.items:
            if "name" not in item or "type" not in item or "fuel_value" not in item or "fuel_category" not in item or len(item) != 4:
                self.throwError(item, "bad columns")
        #recipe columns, and recipe amounts are numbers
        for recipe in self.recipes:
            if "name" not in recipe or "type" not in recipe or "category" not in recipe or "seconds" not in recipe or "ingredients" not in recipe or "results" not in recipe or len(recipe) != 6:
                self.throwError(recipe, "bad columns")
            if type(recipe["seconds"]) not in [int, float]:
                self.throwError(recipe, "bad data types")
            for ingredient in recipe["ingredients"]:
                if "name" not in ingredient or "amount" not in ingredient or len(ingredient) !=2:
                    self.throwError(recipe, "bad ingredient columns")
                if type(ingredient["amount"]) not in [int, float]:
                    self.throwError(recipe, "bad data types")
            for result in recipe["results"]:
                if "name" not in result or "amount" not in result or len(result) !=2:
                    self.throwError(recipe, "bad results columns")
                if type(result["amount"]) not in [int, float]:
                    self.throwError(recipe, "bad data types")

        #all recipes use ingredients and results from the item list
        for recipe in self.recipes:
            for ingredient in recipe["ingredients"]:
                found = False
                for item in self.items:
                    if item["name"] == ingredient["name"]:
                        found = True
                        break
                if found == False:
                    self.throwError(recipe, "recipe contains things not in items")
            for result in recipe["results"]:
                found = False
                for item in self.items:
                    if item["name"] == result["name"]:
                        found = True
                        break
                if found == False:
                    self.throwError(recipe, "recipe contains things not in items")

        #make sure that all items are the result of at least one recipe, except engineer (could check as results and not ingredient)
        for item in self.items:
            found = False
            for recipe in self.recipes:
                inResults = False
                for result in recipe["results"]:
                    if result["name"] == item["name"]:
                        inResults = True
                        break
                if inResults == False: continue
                inIngredients = False
                for ingredient in recipe["ingredients"]:
                    if ingredient["name"] == item["name"]:
                        inIngredients = True
                        break
                if inIngredients == False: 
                    found = True
                    break
            if found == False:
                if item["name"] not in ["tank-machine-gun", "tank-flamethrower", "tank-cannon", "artillery-wagon-cannon", "spidertron-rocket-launcher-1", "spidertron-rocket-launcher-2", "spidertron-rocket-launcher-3", "spidertron-rocket-launcher-4", "vehicle-machine-gun", "dummy-steel-axe", "linked-chest", "linked-belt", "burner-generator", "player-port", "coin", "simple-entity-with-force", "simple-entity-with-owner", "infinity-chest", "infinity-pipe"] and item["name"] not in ("used-up-uranium-fuel-cell", "heat-interface") and item["type"] not in ["engineer", 'item-with-label', 'blueprint', 'copy-paste-tool', 'upgrade-item', 'blueprint-book', 'item-with-tags', 'item-with-inventory', 'deconstruction-item', 'selection-tool']:
                    self.throwError(item, "item not a result (while also not ingredient) of any recipe")
                    print(item["name"])

    def toCsvs(self):
        print("toCsvs not implemented yet")
        pass



myDataParse = dataParse(itemPath, technologyPath, recipePath)

def buildTree():
    pass

def buildReqs(reqs):
    pass
    #reqs is a library of {item name: amount per second}
    #output is library of recipes containing (machine used, [items coming in, blue belts, qty/sec], [items going out, blue belts, qty/sec])











