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

class heuristicParent(clsSubmissionMetadataParent):
    def __init__(self): #we could add name or other args here and **kwargs in the init and super init of the children, but meh. Easier to just set properties aftewards
        super().__init__() #runs the init of template/parent
        
        #assigned by game manager
        self.teamIndex = None #corresponds to the engine player/team list
        #no self.playerIndex because wins are for teams, not players. Don't want confusion.
        self.onlyCurrentPlayer = True #can the heuristic handle only calcs for the current player?


#------Only override these---------

    def getWinProbability(self) -> clsAction:
        """
            Return a number from 0-1 guessing the probability that self.playerIndex (by default is current player) will win
        """
        #or we could return a timeout/forfeit
        eh.error("Child must implement getWinProbability()")

#-------These defs are for the engine/game manager, do not override these---------

    def fallback_prob(self):
        #raising error
        eh.error("Heuristic didn't finish in time")
        # return 0.5 #alternatively we can just do 0.5, but we'd rather fix speed than do that

    def getWinProbability_withintimelimit(self, engine = None, team_index = None):
        self.timedout = False
        resultDict = {} #needs to be mutable container to pass from inner def

        if self.engine is None and engine is None: eh.error("No engine on this heuristic yet")
        if engine is not None: self.engine = engine

        #I think most heuristics will use the current player. This is just in case someone wants to make something extra. But ok to code the heuristic directly using currentPlayer rather than self.playerIndex
        cp = self.engine.GameState.MetadataCurrent.CurrentPlayer
        ct = self.engine.GameState.MetadataInitial.PlayersInitial[cp].Team
        if self.teamIndex is None and team_index is None: #nothing provided, use current player team
            self.teamIndex = ct
        elif team_index is not None: #input provided, use that
            self.teamIndex = team_index
        if self.teamIndex != ct and self.onlyCurrentPlayer == True:
            eh.error("Heuristic can only be used for current player, but is called in other capacity")

        #if the game has been won, skip the big eval
        if self.engine.GameState.MetadataCurrent.WinnerTeam not in [-1, 255, None]:
            if self.teamIndex == self.engine.GameState.MetadataCurrent.WinnerTeam:
                return 1
            else:
                return 0

        def target():
            try:
                resultDict["action"] = self.getWinProbability()
            except Exception:
                resultDict["action"] = None

        t = threading.Thread(target=target)
        t.start()
        t.join(self.timelimit_seconds)

        if t.is_alive():
            # AI took too long
            self.timedout = True
            return self.fallback_prob()

        # It finished in time
        result = resultDict["action"]
        #I can't normalize to within 0-1 without knowing the min and max
        if result > 1 or result < 0: eh.error("Heuristic output not normalized")
        return result
