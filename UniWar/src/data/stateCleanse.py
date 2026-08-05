#takes in a map, standardizes it
#... actually, keep this in engine init maybe??? because of team assignment stuff really would be the only reason.

import numpy as np
from dataclasses import fields

from src.data.gameDataClasses import clsGameState, clsGameData
import src.data.generated_constants as gc



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

    #anything to do here with generic race units?
    #we could check if round>1, then there shouldn't be generic units here
    if myGameState.MetadataCurrent.Round > 1 or myGameState.MetadataCurrent.CurrentPlayer > 0:
        #find generic units
        for unitnum in myGameState.Units.UnitNumbers:
            #lookup race
            race = myGameData.Units[(unitnum, gc.RACENUMBER)]
            if race == 0: raise RuntimeError("Generic unit present after game start")

    return myGameState

    