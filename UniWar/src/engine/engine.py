#the engine has
    # an internal GameState
    # is created from a GameState
    # takes in actions to alter state
    # exposes functions like available moves


#higher level not-AI important stuff can be full classes, not here


from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray
from typing import Optional

from src.gameDataClasses import GameState, GameData

class Engine:
    def __init__(self, gamestate: GameState, gamedata: GameData):
        self.gamestate: GameState = gamestate #is a GameState data class
            #might need to make this private somehow and expose function only? for FOW 
        #probably read rule configs from game state? maybe not
        self.GameData: GameData = gamedata
    
    def getAvailableActions(self):
        #returns list of actions (with their move before and after included) available to all units
        #probably iterates through all units
        availableActions = [] #items are (unit index, ability number, )
        for n, up in self.gamestate.Units.UnitPlayers:
            if up == self.gamestate.MetadataCurrent.CurrentTurn:
                availableActions.append(self.getAvailableActionsUnit(n))
        return availableActions
    
    def getAvailableActionsUnit(self, unit_index):
        #returns list of actions (with their move before and after included) available to unit of given index

        #lookup unit number
        #get a list of all its active abilities - probably build in the loader (or elsewhere) this pre-built as one table
        #for the ones that involve movement, do pathing, attack selection, pathing if relevant

        
        unitnum = self.gamestate.Units.UnitNumbers(unit_index)
        # AvailableActions = 

        return None
    
    def getAvailableMoves(self, unit_index, start_hex_tuple):
        #this can be called on the moveAfterAttack, so unit data will not be of its start movement position
        #start hex tuple is (x, y, state), get the unit type from unit_index
        #returns valid destination hex

        return None
    
    def applyAction(self, action):
        #what is the form of the action?
            #unit index and/or tile x y and state, active ability name perhaps, move to xy, attack index or xystate, final position xystate
        #maybe validate the action is permissible? or not, for speed

        #do we put all the abilities in here, or in separate file?

        pass

    def passTurn(self):
        #alter metadata passing turn
        #generate more rng
        #could put this in the ability file
        pass

# initialState = GameState(metadataInitial=None, map=None, metadataCurrent=None, units=GameUnits(unitNumbers=np.zeroes(10, dtype=np.int8), unitHps=None, unitTiles=None, tileUnits=None))
# print(initialState.units.unitHps)
# myEngine = Engine("stuff")