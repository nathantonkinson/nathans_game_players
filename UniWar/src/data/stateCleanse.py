#takes in a map, standardizes it
#... actually, keep this in engine init maybe??? because of team assignment stuff really would be the only reason.

import numpy as np
from dataclasses import fields

from src.data.gameDataClasses import clsGameState, clsGameData
import src.data.generated_constants as gc
import src.errorHandler as eh



def stateCleanse(myGameState: clsGameState, myGameData: clsGameData) -> clsGameState:
    #takes in a gamestate (intended to be freshly loaded maps), and outputs a new cleaned version
    #we could just mutate in the place the one given, which is largely what we do. The return is just a pointer too probably.

    #Team assignment. If no teams, ffa
    nonblankTeam = False
    for p, player in enumerate(myGameState.MetadataInitial.PlayersInitial):
        if player.Race is None: raise RuntimeError("Race unassigned at engine start")
        if player.Team is None:
            if nonblankTeam == True: raise RuntimeError("Teams partially assigned at engine start") 
            player.Team = p #teams are indexed at 0. Idk how this can mutate since the PlayersInitial is frozen... hm.
        else:
            nonblankTeam = True

    #units size reshaping
    for f in fields(myGameState.Units):
        old_array = getattr(myGameState.Units, f.name)
        fullof = 255 if f.name != "UnitActions" else 1
        fullshape = 255 if f.name != "UnitHexes" else (255, 3)
        fullsize = np.full(fullshape, fullof, dtype=np.uint8)
        fullsize[:old_array.shape[0]] = old_array
            # new[:old.shape[0], :old.shape[1]] = old
            # new = np.pad(old, (0, 255 - old.size), mode='constant', constant_values=1)
        setattr(myGameState.Units, f.name, fullsize)

    #anything to do here with generic race units? Those mostly handled upon game start by player choice or gameManager/tournament manager
    #we could check if round>1, then there shouldn't be generic units here
    if myGameState.MetadataCurrent.Round > 1 or myGameState.MetadataCurrent.CurrentPlayer > 0:
        #find generic units
        for unitnum in myGameState.Units.UnitNumbers:
            #lookup race
            race = myGameData.Units[(unitnum, gc.RACENUMBER)]
            if race == 0: eh.error("Generic unit present after game start")

    #check that if there is no BasePlayers, there are no bases. And that it is the same dims as the map
    if myGameState.Map.BasePlayers is not None:
        if myGameState.Map.BasePlayers.shape != myGameState.Map.Map.shape: eh.error("baseplayers present and not same shape as map")
    else:
        for x, col in enumerate(myGameState.Map.Map):
            for y, terrainnum in enumerate(col):
                if terrainnum in (2, 15): #harbor, base
                    eh.error("Bases or harbors present but no BasePlayers provided in map")

    #initialize playersCredits and playersKills if that hasn't been done
    eh.warning("Need to initialize playerscredits and playerskills")
    dtype = next(f.metadata["dtype"] for f in fields(type(myGameState.MetadataCurrent)) if f.name == "PlayersKills")
    if myGameState.MetadataCurrent.PlayersKills is None:
        myGameState.MetadataCurrent.PlayersKills = np.full(len(myGameState.MetadataInitial.PlayersInitial), 0, dtype=dtype)
    dtype = next(f.metadata["dtype"] for f in fields(type(myGameState.MetadataCurrent)) if f.name == "PlayersCredits")
    if myGameState.MetadataCurrent.PlayersCredits is None:
        myGameState.MetadataCurrent.PlayersCredits = np.full(len(myGameState.MetadataInitial.PlayersInitial), 0, dtype=dtype)

    return myGameState

    