import threading
import sys
import os
from pathlib import Path
import numpy as np

import src.data.generated_constants as gc
from src.data.gameDataClasses import clsGameState, clsGameData, clsAction
from src.engine.engine import clsEngine
from src.engine.submissionMetadataParent import clsSubmissionMetadataParent
import src.errorHandler as eh

#Things to add - ... i don't know.
#Logging?
#Methods for accessing heuristic and search functions
#Do random action or pass turn on timeout
#How to specify what hashtags or specific maps (and players within the map) etc the player is valid for

class playerParent(clsSubmissionMetadataParent):
    def __init__(self): #we could add name or other args here and **kwargs in the init and super init of the children, but meh. Easier to just set properties aftewards
        super().__init__() #runs the init of template/parent
        
        #assigned by game manager
        self.playerIndex = None #corresponds to the engine player list

#------Only override these---------

    def choose_action(self) -> clsAction:
        """
            Return clsAction from the engine.availableActions list. 
            Child classes override this (meaning you need to make a def named "choose_action" in your player class)
            Use the self.engine as data on the current state of the game
        """
        #or we could return a timeout/forfeit
        eh.error("Child AI must implement choose_action()")

    #you can override this or leave it be
    def choose_race(self) -> int:
        """
            Having the GameState (map), choose a race. Random within your parameters by default
            This will not be called if the map forces a race, and it is within your allowed. 
        """
        #random from preferred if allowed, otherwise random from allowed
        if self.allowedRaces:
            raceList = self.allowedRaces
        if self.engine.GameState.MetadataInitial.AllowedRaces:
            raceList = raceList & self.engine.GameState.MetadataInitial.AllowedRaces
        if self.engine.GameState.MetadataInitial.Players[self.playerIndex].AllowedRaces:
            raceList = raceList & self.engine.GameState.MetadataInitial.Players[self.playerIndex].AllowedRaces
        if len(raceList) == 0: eh.error("Player is not valid for the available races")
        if self.preferredRaces: availablePreferred = raceList & self.preferredRaces
        randomFromRaces = availablePreferred if len(availablePreferred) > 0 else raceList
        return np.random.choice(randomFromRaces)

#-------These defs are for the engine/game manager, do not override these---------

    def fallback_action(self) -> clsAction:
        eh.error("Player hit fallback") #we'd rather fix speed than use fallbacks

        # #we are doing surrender instead of pass turn or random or action0 because I don't want to accumulate a bunch of threads that are taking forever.
        # surrender = clsAction(255, gc.SURRENDER, (0,0,gc.DEFAULTALTITUDE), 255, (0,0, gc.DEFAULTALTITUDE))
        # if surrender not in self.engine.availableActions:
        #     eh.error("surrender not in available actions")
        # return surrender

    def choose_action_withtimelimit(self) -> clsAction:
        self.timedout = False
        resultDict = {} #needs to be mutable container to pass from inner def

        if self.engine is None: eh.error("No engine on this player yet")
        if self.playerIndex is None: eh.error("No player index assigned to this player")
        # print(self.playerIndex)
        if self.playerIndex != self.engine.GameState.MetadataCurrent.CurrentPlayer:
            eh.error(f"Not my turn. player index = {self.playerIndex}")

        def target():
            try:
                resultDict["action"] = self.choose_action()
            except Exception:
                resultDict["action"] = None

        t = threading.Thread(target=target)
        t.start()
        t.join(self.timelimit_seconds)

        if t.is_alive():
            # AI took too long
            self.timedout = True
            return self.fallback_action()

        # AI finished in time - was it a valid action?
        result = resultDict["action"]
        if result in self.engine.availableActions:
            return result
        else:
            eh.error("chosen action not in available list", result, self.engine.availableActions)
            return self.fallback_action() #invalid, use fallback action