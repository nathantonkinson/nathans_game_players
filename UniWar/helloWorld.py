from dataclasses import dataclass, is_dataclass, fields
import numpy as np
import sys
import time

#these are individual files. I want to import all classes from them. Idk if this is best practice.
from src.data.loader import Loader
# import src.gameDataClasses as dc
import src.data.generated_constants as gc
from src.data.gameDataClasses import GameData, GameState, clsAction, clsHex
import src.data.flattening as f
from src.engine.engine import Engine



myLoader = Loader()
myGameData: GameData = myLoader.load_GameData()
myGameState: GameState = myLoader.load_map("plainsLine.yaml")
myEngine: Engine = Engine(myGameState, myGameData)
myGameData = f.allFlattening(myGameData)


# #DO THE ATTACK MANUALLY
# print(myGameState.Units.UnitHexes)
# print(myGameState.Units.UnitHps)
# myAction = clsAction(0, 1, clsHex(0, 2, 1), 1, clsHex(0, 2, 1))
# myEngine.applyAction(myAction)
# print(myGameState.Units.UnitHexes)
# print(myGameState.Units.UnitHps)

#don't forget data validation
#and map cleansing, maybe
            

#might be a good exercise to run every unit on every terrain vs every unit on every terrain
    #technically for generating all possible p values, but also just good exercise



