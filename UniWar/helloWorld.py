from dataclasses import dataclass, is_dataclass, fields

#these are individual files. I want to import all classes from them. Idk if this is best practice.
from src.loader import Loader
from src.gameDataClasses import GameData, GameState
from src.engine.engine import Engine



#we should be able to avoid calling AvailableMoves again if no enemy units killed. Just can't move into place previous piece did, and new spot maybe opened up? So available moves should include friendly spaces? (and maybe enemy too, if doesn't violate ZOC)
#should we do cleansing before loading to data classes, or after?

myLoader = Loader()

myGameData: GameData = myLoader.load_gameData()
myGameState: GameState = myLoader.load_map("plainsLine.yaml")
myEngine: Engine = Engine(myGameState, myGameData)


# print(myEngine.GameData.)

#let's do the HexUnits cleansing at some point





#don't forget validation

#let's now manually send actions to the engine
#the engine has an internal GameState, is created from a GameState, takes in actions to alter state, exposes functions like available moves

#let's check