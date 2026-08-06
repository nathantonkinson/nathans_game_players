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
from src.data.gameDataClasses import clsGameData, clsGameState, clsAction, clsLoc
import src.data.flattening as f
from src.engine.engine import Engine
from src.visualizer.visualizer import Visualizer #lol folder, filename, and class are all the same
from src.data.stateCleanse import stateCleanse
from players.playerRandom import clsPlayerRandom
from players.playerFirstchoice import clsPlayerFirstchoice #maybe need to do something special so we have access to all of these, or can do more like a list
from src.engine.gameManager import clsGameManager
from src.data.writeConstants import write_constants_file


#region run manually
# #RUN MANUALLY
# myLoader = Loader()
# myGameData: clsGameData = myLoader.load_GameData()
# write_constants_file(myGameData)
# myGameData = f.allFlattening(myGameData)
# myGameState: clsGameState = myLoader.load_map("plainsLine")
# myGameState = stateCleanse(myGameState, myGameData) #must call outside of loader due to GameData
# myEngine: Engine = Engine(myGameState, myGameData)

# print(myEngine.getDist(0, 0, 0, 1))
# print(myEngine.getDist(0, 2, 0, 3))

# myEngine.applyAction(clsAction(0, 24, (0, 2, 1), 255, (0, 2, 1)))
# myEngine.applyAction(clsAction(255, 26, (0, 0, 1), 255, (0, 0, 1)))
# myEngine.applyAction(clsAction(255, 26, (0, 0, 1), 255, (0, 0, 1)))
# print(myEngine.availableActions)
# myEngine.applyAction(clsAction(0, 1, (0, 2, 1), 1, (0, 2, 1)))
# print(myEngine.GameState.MetadataCurrent.WinnerTeam)
#endregion run manually



# myLoader = Loader()
# myLoader.load_map("plainsLine")

# Player1 = clsPlayerFirstchoice()
# Player2 = clsPlayerFirstchoice()
Player1 = clsPlayerRandom()
Player2 = clsPlayerRandom()
myGameManager = clsGameManager()
write_constants_file(myGameManager.GameData) #don't need to run this every time, could put it in a utility packet
myGameManager.setMap(mapFilename="plainsLine", playerListInstance=[Player1, Player2])
myGameManager.play(gameCount=100)



#ok now let's do:
#game logging for replays and ai training and whatnot
#something to see all possible combos of moves/actions on a turn, maybe then plug into visualizer
#a very basic static heuristic (credits)
#more complicated maps and units (not doing any specials yet - no plague, no underlings or subs, no bases, no conversions)
#see if we can get a CPU of any kind of solve tank vs plasma or something similar, or even the 10 vs 1 for that matter.
#   two marines on swamp with a mountain in between
#automatically detect changes to player files and increment their version?

# myViz = Visualizer(myGameData, myGameState, myEngine) #we should actually only need to pass the engine, right?
# myViz.run()


#don't forget data validation
#there's more opportunity in map cleansing
#use np arrays instead of cls loc perhaps? So available actions will be a numpy? But then it would have to be added to gradually... idk. It's just one of the most common things we do.

            

#might be a good exercise to run every unit on every terrain vs every unit on every terrain
    #technically for generating all possible p values, but also just good exercise


# if __name__ == "__main__": print("I'm main") #in other files prints something like src.data.gameDataClasses

#Structure seems a little too deep
#GameManager
    #Engine
        #GameData
        #GameState
#we could make the engine reference the GameManager
#but I do like the ability to use Engine all on it's own.

