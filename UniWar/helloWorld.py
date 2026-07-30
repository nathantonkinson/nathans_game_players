from dataclasses import dataclass, is_dataclass, fields
import numpy as np
import sys
import time #time.time() #in seconds
import os
import cProfile # cProfile.run("helloWorld()", sort="tottime")

#these are individual files. I want to import all classes from them. Idk if this is best practice.
from src.data.loader import Loader #this file has file tree navigation stuff btw
# import src.gameDataClasses as dc
import src.data.generated_constants as gc
from src.data.gameDataClasses import GameData, GameState, clsAction, clsLoc, write_constants_file
import src.data.flattening as f
from src.engine.engine import Engine
from src.visualizer.visualizer import Visualizer #lol folder, filename, and class are all the same
# import src.visualizer.visualizer_test

# if __name__ == "__main__": print("I'm main") #in other files prints something like src.data.gameDataClasses

myLoader = Loader()
myGameData: GameData = myLoader.load_GameData()
myGameData = f.allFlattening(myGameData)
write_constants_file(myGameData) #don't need to run this every time, could put it in a utility packet
myGameState: GameState = myLoader.load_map("plainsLine.yaml")
myEngine: Engine = Engine(myGameState, myGameData)

myEngine.getAvailableActions()
print(myEngine.availableActions)

# myViz = Visualizer(myGameData, myGameState, myEngine) #we should actually only need to pass the engine, right?
# myViz.run()

# #DO THE ATTACK MANUALLY
# print(myGameState.Units.UnitHexes)
# print(myGameState.Units.UnitHps)
# myAction = clsAction(0, 1, clsLoc(0, 2, 1), 1, clsLoc(0, 2, 1))
# myEngine.applyAction(myAction)
# print(myGameState.Units.UnitHexes)
# print(myGameState.Units.UnitHps)

#don't forget data validation
#and map cleansing, maybe
#use np arrays instead of cls loc perhaps? So available actions will be a numpy? But then it would have to be added to gradually... idk. It's just one of the most common things we do.
#call for moves only once per unit?
#getGexesInRange -dist_max got overflow warning
            

#might be a good exercise to run every unit on every terrain vs every unit on every terrain
    #technically for generating all possible p values, but also just good exercise



