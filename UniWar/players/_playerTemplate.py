import threading
import sys
import os
from pathlib import Path
import numpy as np

import src.data.generated_constants as gc
from src.data.gameDataClasses import clsGameState, clsGameData, clsAction
from src.engine.engine import Engine


#Things to add - ... i don't know.
#Logging?
#Methods for accessing heuristic and search functions
#Do random action or pass turn on timeout
#How to specify what hashtags or specific maps (and players within the map) etc the player is valid for

class playerTemplate:
    def __init__(self): #we could add name or other args here and **kwargs in the init and super init of the children, but meh. Easier to just set properties aftewards
        #when you make the child, your CPU player, these will be the default values unless/until you set them in your own init

        #filename shennanigans
        module = sys.modules[self.__class__.__module__]
        # self.filepath = module.__file__
        # self.filenamewithmod = self.__class__.__module__ #this will get you "players.[filename]"
        # self.filename = os.path.basename(module.__file__)
        path = Path(module.__file__)
        self.filepath = str(path)
        self.filestem = path.stem #MyPlayer"
        # self.filename = path.name   # "MyPlayer.py"

        #initializations of optional metadata people can fill in
        self.name = self.filestem #used for display, differenatiation of multiple instances of same player class, I will edit name from outside
        self.description = f"(No description)" #could do f"{self.filestem} (no description)""
        self.author = "(No author given)" #this should be uniwar username
        self.version = "(No version given)" #useful perhaps if we are doing genetic algorithms or something... 
            #ugh I want players without init arguments but if I want a generic player that takes in a kind of neural net of which there are many variants... ugh
        self.allowedRaces = {1, 2, 3} #will exclude this player from games that require them to be a player not in this list
        self.preferredRaces = {} #if given the choice, will pick randomly from this list
        self.excludedHashtags = {"RNGBUILD", "RNGBUILDANY", "EDITSTATS"}
        self.requiredHashtags = {} #if limited player, things like #NOREPAIR or something that limits to one unit type

        #assigned by game manager
        self.engine: Engine = None
        self.playerIndex = None #corresponds to the engine player list
        self.timedout = False #is set to true if your choose_action does not return within the time allotted, the game manager will detect this and make you forfeit.
        self.timelimit_seconds = 60 #I guess we're defaulting to 1 minute per action if game manager doesn't set it for us
        self.race = None

#------Only override this---------

    def choose_action(self) -> clsAction:
        """
            Return clsAction from the engine.availableActions list. 
            Child classes override this (meaning you need to make a def named "choose_action" in your player class)
            Use the self.engine as data on the current state of the game
        """
        #or we could return a timeout/forfeit
        raise NotImplementedError("Child AI must implement choose_action()")

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
        if len(raceList) == 0: raise RuntimeError("Player is not valid for the available races")
        if self.preferredRaces: availablePreferred = raceList & self.preferredRaces
        randomFromRaces = availablePreferred if len(availablePreferred) > 0 else raceList
        return np.random.choice(randomFromRaces)


#-------These defs are for the engine/game manager, do not override these---------

    def fallback_action(self) -> clsAction:
        #we are doing surrender instead of pass turn or random or action0 because I don't want to accumulate a bunch of threads that are taking forever.
        surrender = clsAction(255, gc.SURRENDER, (0,0,gc.DEFAULTALTITUDE), 255, (0,0, gc.DEFAULTALTITUDE))
        if surrender not in self.engine.availableActions:
            raise RuntimeError("surrender not in available actions")
        return surrender

    def choose_action_withtimelimit(self) -> clsAction:
        self.timedout = False
        resultDict = {} #needs to be mutable container to pass from inner def

        if self.engine is None: raise RuntimeError("No engine on this player yet")
        if self.playerIndex is None: raise RuntimeError("No player index assigned to this player")
        # print(self.playerIndex)
        if self.playerIndex != self.engine.GameState.MetadataCurrent.CurrentPlayer:
            raise RuntimeError(f"Not my turn. player index = {self.playerIndex}")

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
            print("chosen action not in available list", result, self.engine.availableActions)
            return self.fallback_action() #invalid, use fallback action