#the engine has
    # an internal GameState
    # is created from a GameState
    # takes in actions to alter state
    # exposes functions like available moves


#higher level not-AI important stuff can be full classes, not here


from dataclasses import dataclass


@dataclass
class GameState:
    def __init__(self):
        self.metadataInitial = None
        self.map = None
        self.metadataCurrent = None
        self.units = None

class Engine:
    def __init__(self, gamestate):
        self.gamestate = gamestate #is a GameState data class
            #might need to make this private somehow and expose function only? for FOW
        #probably read rule configs from game state? maybe not
    
    def getAvailableActions(self):
        #returns list of actions (with their move before and after included) available to all units
        #probably iterates through all units
        return None
    
    def getAvailableActionsUnit(self, unit_index):
        #returns list of actions (with their move before and after included) available to unit of given index

        #lookup unit number
        #get a list of all its active abilities
        #for the ones that involve movement, do pathing

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