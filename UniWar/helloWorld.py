from src.loader import Loader
from src.engine.dataClasses import GameState

myLoader = Loader()
gameData = myLoader.load_gameData()
mapdata = myLoader.load_map("plainsLine.yaml")


# print(gameData) #a dict, one entry per table. Each table is a list of dicts with idenical keys
# print(mapdata.metadataInitial)




#don't forget validation

#let's now manually send actions to the engine
#the engine has an internal GameState, is created from a GameState, takes in actions to alter state, exposes functions like available moves

#let's check