#takes in a map, standardizes it
#... actually, keep this in engine init maybe??? because of team assignment stuff really would be the only reason.

import numpy as np
from dataclasses import fields

from src.data.gameDataClasses import clsGameState, clsGameData, clsGUB, clsMetadataCurrent
import src.data.generated_constants as gc
import src.errorHandler as eh



def stateCleanse(myGameState: clsGameState, myGameData: clsGameData) -> clsGameState:
    #takes in a gamestate (intended to be freshly loaded maps), and outputs a new cleaned version
    #we could just mutate in the place the one given, which is largely what we do. The return is just a pointer too probably.

    #metadata current needs to be initialized?? 
    gameStarted = False
    noMetadataCurrent = False
    if myGameState.MetadataCurrent is None:
        noMetadataCurrent = True
        qtyPlayers = len(myGameState.MetadataInitial.PlayersInitial)
        myGameState.MetadataCurrent = clsMetadataCurrent(
            PlayersCredits=np.full(qtyPlayers, 0, dtype=np.uint16)
            , PlayersKills=np.full(qtyPlayers, 0, dtype=np.uint32)
            , WinnerTeam=None
            , RandomState={}
            , CurrentPlayer=0
            , CurrentRound = 1
            , CurrentAction = 1
            , GangUpBonus=clsGUB()
        )

    #detect no moves made yet. Round1,cp=0 and all units of currentplayer have their appropriate actions
    cp = myGameState.MetadataCurrent.CurrentPlayer
    # print(cp, myGameState.MetadataCurrent.CurrentRound)
    if myGameState.MetadataCurrent.CurrentRound != 1 or cp != 0 or myGameState.MetadataCurrent.CurrentAction != 1: gameStarted = True
    if gameStarted == False: #we are at first turn, but have any units acted?
        #check all units of current player have full actions
        for u, up in enumerate(myGameState.Units.UnitPlayers):
            if up != cp: continue
            un = myGameState.Units.UnitNumbers[u]
            ua = myGameState.Units.UnitActions[u]
            if ua < myGameData.Units[(un, gc.ACTIONSPERTURN)]:
                gameStarted = True
                if noMetadataCurrent == True: eh.error("No metadata current but actions are not full")
                break

    #Team assignment. If no teams, ffa
    eh.warning("State cleanse before or after players when init? And include conditions for game start?")
    nonblankTeam = False
    teams_present = [0]*len(myGameState.MetadataInitial.PlayersInitial)
    for p, player in enumerate(myGameState.MetadataInitial.PlayersInitial):
        if player.Race is None: eh.error("Race unassigned at engine start") #but... are we going to call this cleanse before or after loading players??
        if player.Team is None:
            if nonblankTeam == True: eh.error("Teams partially assigned at engine start") 
            player.Team = p #teams are indexed at 0. Idk how this can mutate since the PlayersInitial is frozen... hm.
        else:
            nonblankTeam = True
        teams_present[player.Team] = 1
    #check teams goes up from 0 continuously
    reached_end = False
    for presence in teams_present:
        if presence == 0: 
            reached_end = True
        else:
            if reached_end == True: eh.error("Teams don't continuously go up from 0")

    #units size reshaping - not doing due to copy nonsense. Instead resize when new units created, and reuse old slots after death. Probs never downsize.
    # for f in fields(myGameState.Units):
    #     old_array = getattr(myGameState.Units, f.name)
    #     fullshape = 255 if f.name != "UnitHexes" else (255, 3)
    #     if old_array.shape == fullshape: continue #already correct shape
    #     fullof = 255 if f.name != "UnitActions" else 1
    #     fullsize = np.full(fullshape, fullof, dtype=np.uint8)
    #     fullsize[:old_array.shape[0]] = old_array
    #         # new[:old.shape[0], :old.shape[1]] = old
    #         # new = np.pad(old, (0, 255 - old.size), mode='constant', constant_values=1)
    #     setattr(myGameState.Units, f.name, fullsize)

    #check that if there is no BasePlayers, there are no bases.
    #check shape of BasePlayers
    if myGameState.BasePlayers is not None:
        if myGameState.BasePlayers.shape[1] != 3 or myGameState.BasePlayers.ndim != 2: eh.error("baseplayers present and (x, y, p)*qtyBases")
        #check all bases and harbors accounted for
        eh.warning("State cleanse needs to check that BasePlayers accounts for all bases and harbors")
    else:
        myGameState.BasePlayers = np.full((0, 3), 255, dtype=np.uint8) #empty array of right size
        eh.warning("State cleanse needs to check that BasePlayers accounts for all bases and harbors")
        for x, col in enumerate(myGameState.Map):
            for y, terrainnum in enumerate(col):
                if terrainnum in (2, 15): #harbor, base
                    eh.error("Bases or harbors present but no BasePlayers provided in map")
        #no bases or harbors... keep it None?
        # myGameState.BasePlayers = np.full((1, 3), 255, dtype=np.uint8)

    #initialize playersCredits and playersKills if that hasn't been done
    eh.warning("Need to initialize playerscredits and playerskills")
    dtype = next(f.metadata["dtype"] for f in fields(type(myGameState.MetadataCurrent)) if f.name == "PlayersKills")
    if myGameState.MetadataCurrent.PlayersKills is None:
        if gameStarted == True: eh.error("Game already started and playerKills not initialized??")
        myGameState.MetadataCurrent.PlayersKills = np.full(len(myGameState.MetadataInitial.PlayersInitial), 0, dtype=dtype)
    dtype = next(f.metadata["dtype"] for f in fields(type(myGameState.MetadataCurrent)) if f.name == "PlayersCredits")
    if myGameState.MetadataCurrent.PlayersCredits is None:
        if gameStarted == True: eh.error("Game already started and playerCredits not initialized??")
        myGameState.MetadataCurrent.PlayersCredits = np.full(len(myGameState.MetadataInitial.PlayersInitial), 0, dtype=dtype)

    #GUB
    if gameStarted == False:
        if myGameState.MetadataCurrent.GangUpBonus == None:
            myGameState.MetadataCurrent.GangUpBonus = clsGUB() #does defaults
        elif myGameState.MetadataCurrent.GangUpBonus.DefenderIndex not in (-1, 255, None):
            eh.error("Game not started and GUB has nonempty values")
    
    #throw errors if generic units found after gameStarted
    if gameStarted == True:
        #find generic units
        for unitnum in myGameState.Units.UnitNumbers:
            if unitnum in (0, -1, 255, None): continue
            #lookup race
            race = myGameData.Units[(unitnum, gc.RACENUMBER)]
            if race == 0: eh.error("Generic unit present after game start")

    eh.warning("Check no units are on same location, in location they can't exist, etc")

    
    #If no city credits provided, it's half base round to 5
    #base credits are available from 25 to 150 in increments of 25
    #initial credits are available from 0 to 2500 in increments of 50
    if myGameState.MetadataInitial.CityCredits == None:
        bc = myGameState.MetadataInitial.BaseCredits
        cc = int((bc / 2 + 2.5) // 5 * 5) #// does a floor to multiple of 5
        myGameState.MetadataInitial.CityCredits = cc

    return myGameState

    