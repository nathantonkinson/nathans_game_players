from dataclasses import dataclass, is_dataclass, fields
import numpy as np
import sys
import time #time.time() #in seconds
import os
import cProfile # cProfile.run("helloWorld()", sort="tottime")
import copy
from math import comb
import math

#these are individual files. I want to import all classes from them. Idk if this is best practice.
from src.data.loader import Loader #this file has file tree navigation stuff btw
# import src.gameDataClasses as dc
import src.data.generated_constants as gc
from src.data.gameDataClasses import *
import src.data.flattening as f
from src.engine.engine import clsEngine
from src.visualizer.visualizer import Visualizer #lol folder, filename, and class are all the same
from src.data.stateCleanse import stateCleanse
from players.playerRandom import clsPlayerRandom
from players.playerFirstchoice import clsPlayerFirstchoice #maybe need to do something special so we have access to all of these, or can do more like a list
from src.engine.gameManager import clsGameManager
from src.data.writeConstants import write_constants_file
from heuristics.creditProp import creditProp


#region run manually

myLoader = Loader()
myGameData: clsGameData = myLoader.load_GameData()
write_constants_file(myGameData)
myGameData = f.allFlattening(myGameData)
myGameState: clsGameState = myLoader.load_map("TwoMarines")
myGameState = stateCleanse(myGameState, myGameData) #must call outside of loader due to GameData
myEngine: clsEngine = clsEngine(myGameState, myGameData)
myEngine.Initialization()


#region copy plan, speed ideas, speed testing
#MINIMAL COPY (storage is a different question)
    #set/dictionary of:
    #V1 
        #(within one turn)
            #Units (hps, players, etc)
            #Metadata: 
            #   Kills (not important but unavoidable I think - unless we want to track a bunch of other stats and better to replay actions)
            #   randomState/rng object, GUB - so maybe make it just tuple stuff
            #Action# technically not needed but probs super helpful
        #(added for across turns)
            #Metadata: round, current player, player credits, base players
    #V2 ??? only actions? but then engine would need to replay up to current, not good
    #V3 ??? only a weird list of deltas? If a lot changes, not good, and essentially similar to storing actions
#by one instance and refs to it we will have GameData, map.map, metadatainitial
#MINIMAL STORAGE (is this important?)
    #set/dictionary of:
    #V1
        #action list
    #V2
        #parent action index, action, depth num (derivable from parent chain but probably should have it to identify terminals)

#SPEED IDEAS:
#incremental changes to availableActions and helper arrays
#replace deepCopy with something else
    #MetadataCurrent
    #rng
    #availableActions - might need to switch to struct of arrays
    #in engine move after attack
#identical state but later round dedup
#identical state but other player dedup
#trimming bad heuristic decisions etc

#SPEED TESTING
#TwoMarines original:
    # 2 = 109 for 0.3 seconds
    # 3 = 481 for 1.5 seconds
    # 5 = 17221 for 52 seconds
    # 7 = 572k for 1657 seconds (27 minutes)
#set helpers to copy, remove all deepcopies from clone, recalc actions vs deepcopy it.
    # 5 = 17221 for 93 seconds :(
#switch available actions back to a deepcopy
    # 5 = 17221 for 68 seconds, 
    # with cProfile, 5 = 3.62 for getHexesInRange
#using np getHexesInRange (no effect)
    # with cPRofile, 5 = 3.63 for getHexesInRange_np
#turned off unit helper arrays, kept and functionized the loc ones.
    # 5 = 17221 for 55 seconds, nice reduced a little
#changed availableActions to a nparray, but now maybe more copying load? idk
    # 5 = 17221 for 55 seconds
#leave units arrays at length 4 instead of 255, resize as needed
    # 5 = 17221 for 23 seconds
#remove surrender
    # 5 - 14704 for 25 seconds
#Now that available actions is a nparray, use .copy() on it
    # 5 - 14704 for 25 seconds :( no advantages?
#Not using loc helpers:
    # 5 - 14704 for 30 seconds. I think we'll keep using the loc helpers due to O(n) problems and we are small scale right now
#endregion

possibleStates: dict = {} #key = action sequence??, value = state?
possibleStates: list[clsNode] = [] #full of (action sequence, engine, heuristic output, stability output, +??)
myHeuristic = creditProp()
def clone_engine(engine: clsEngine, turn_transition = False) -> clsEngine:
    #ndarray.copy much faster than deepcopy, so each individual
    new_units: clsGameUnits = clsGameUnits(
         UnitPlayers = engine.GameState.Units.UnitPlayers.copy()
         , UnitNumbers = engine.GameState.Units.UnitNumbers.copy()
         , UnitHps = engine.GameState.Units.UnitHps.copy()
         , UnitHexes = engine.GameState.Units.UnitHexes.copy()
         , UnitActions = engine.GameState.Units.UnitActions.copy()
    )

    mc_old = engine.GameState.MetadataCurrent
    new_gub = clsGUB(
        DefenderIndex=mc_old.GangUpBonus.DefenderIndex
        , AttackerLoc=mc_old.GangUpBonus.AttackerLoc #tuples are immutable, so no copy method available or needed. Also whenever we change it, we set it to a new class instance
        )
    if turn_transition:
        new_basePlayers = engine.GameState.BasePlayers.copy()
        new_metadatacurrent = clsMetadataCurrent(
            #not used except during load
            # RandomState = mc_old.RandomState.copy()
            #simples (by ref doesn't matter)
            CurrentPlayer = mc_old.CurrentPlayer
            , Round = mc_old.CurrentRound
            , Action = mc_old.CurrentAction
            , WinnerTeam = mc_old.WinnerTeam
            #Lists that need to be copied on turn transition
            , PlayersCredits = mc_old.PlayersCredits.copy()
            #Lists that are going to change per action anyway
            , PlayersKills = mc_old.PlayersKills.copy()
            , GangUpBonus = new_gub #in turn transition, should be blank, so... could just do clsGUB() or new_gub... idk if it matters   
        )
    else:
        new_basePlayers = engine.GameState.BasePlayers
        new_metadatacurrent = clsMetadataCurrent(
            #not used except during load
            # RandomState = mc_old.RandomState.copy()
            #simples (by ref doesn't matter)
            CurrentPlayer = mc_old.CurrentPlayer
            , CurrentRound = mc_old.CurrentRound
            , CurrentAction = mc_old.CurrentAction
            , WinnerTeam = mc_old.WinnerTeam
            #Lists that need to be copied on turn transition, but not now
            , PlayersCredits = mc_old.PlayersCredits
            #Lists that are going to change per action anyway
            , PlayersKills = mc_old.PlayersKills.copy()
            , GangUpBonus = new_gub
        )
    
    new_state: clsGameState = clsGameState(
        #IMMUTABLE
        Map = engine.GameState.Map                     
        , MetadataInitial = engine.GameState.MetadataInitial
        #, GameData = state.GameData #probably keep this outside of state given that it is map/game independent

        #MUTABLE PER ACTION (copy)
        , MetadataCurrent = new_metadatacurrent
            #this has some per action, some per turn, some per round
        , Units = new_units
        #MUTABLE PER TURN
        , BasePlayers = new_basePlayers 
    )
    new_engine = clsEngine(new_state, engine.GameData)

    new_engine.rng = np.random.default_rng() 
    new_engine.rng.bit_generator.state = engine.rng.bit_generator.state.copy()
    new_engine.roundlimit = engine.roundlimit #a scalar

    new_engine.useHelperArraysUnits = engine.useHelperArraysUnits
    if engine.useHelperArraysUnits:
        new_engine.unitDefenses = engine.unitDefenses.copy()
        new_engine.unitMobility = engine.unitMobility.copy()
        new_engine.unitAttackrangemin = engine.unitAttackrangemin.copy()
        new_engine.unitAttackrangemax = engine.unitAttackrangemax.copy()
    new_engine.useHelperArraysLocs = engine.useHelperArraysLocs
    if engine.useHelperArraysLocs:
        new_engine.locUnits = engine.locUnits.copy()
        new_engine.locZoc = engine.locZoc.copy() #hm, copy here, mutate when enemies die.. hm.

    if turn_transition:
        # new_engine.locPlayers = engine.locPlayers.copy()
        new_basePlayers = engine.GameState.BasePlayers.copy() #ndarray copy method
    else:
        # new_engine.locPlayers = engine.locPlayers
        new_basePlayers = engine.GameState.BasePlayers

    # new_engine.getAvailableActions() #make this struct of arrays? mutate, etc idk.
    new_engine.availableActions = engine.availableActions.copy()

    #the engine does replace GameData when it handles norepair hashtag, but that's only in initialization

    return new_engine
def searchFlex(startEngine: clsEngine, max_depth: int):
    cp = startEngine.GameState.MetadataCurrent.CurrentPlayer
    ct = startEngine.GameState.MetadataInitial.PlayersInitial[cp].Team
    frontier: list[clsNode] = []
    frontier.append(clsNode(
        ParentNode = None
        , Depth = 0
        , NodeEngine = clone_engine(startEngine)
        , Heuristic = myHeuristic.getWinProbability_withintimelimit(startEngine)
    ))

    while frontier: #while list has items in it
        node = frontier.pop()
        # print(node.Action)
        # if np.array_equal(node.Action, [1, 24, 255, 1,   0, 1, 1,   0, 1, 1]):
        #     print(node.NodeEngine.availableActions)
        for a, action in enumerate(node.NodeEngine.availableActions):
            branchEngine = clone_engine(node.NodeEngine)
            # if np.array_equal(action, [1, 24, 255, 1,   0, 1, 1,   0, 1, 1]) and node.NodeEngine.GameState.MetadataCurrent.CurrentAction == 1:
            #     # print(node.NodeEngine.availableActions)
            #     print(branchEngine.availableActions)
            #     print(branchEngine.GameState)
            branchEngine.applyAction(action)
            heuristicVal = myHeuristic.getWinProbability_withintimelimit(engine = branchEngine, team_index = ct) #no need for deepcopy
            branchNode = clsNode(
                ParentNode = node #action sequence
                , NodeEngine = branchEngine
                , Heuristic = heuristicVal
                , Depth = node.Depth + 1
                , Action = action
            )
            possibleStates.append(branchNode)
            if node.Depth + 1 < max_depth:
                if branchEngine.GameState.MetadataCurrent.WinnerTeam in [-1, 255, None]: #don't keep searching once game is won
                    frontier.append(branchNode)


myEngine.Initialization()
startTime = time.time()
print("Starting...")
# # cProfile.run("searchFlex(clone_engine(myEngine), 5) ", sort="tottime")
searchFlex(clone_engine(myEngine), 5) 
#     #5*6
#     #6*5+1
#     #1*(6+5+1)
#     #(5+6)*1
duration = time.time() - startTime
print(f"Possible states qty: {len(possibleStates)}, calculation seconds = {duration}")

# def displayFull(inputPossibleStates):
#     result = []
#     for node in inputPossibleStates:
#         tempnode: clsNode = node
#         actionlist = []
#         while tempnode is not None:
#             if tempnode.Action is not None:
#                 actionlist.append((tempnode.Action[gc.UNITINDEX], tempnode.Action[4], tempnode.Action[5]))
#             tempnode = tempnode.ParentNode
#         actionlist = actionlist[::-1] #reversing it. Can also .reverse(), or list(reversed(my_list))
#         result.append((
#             node.Depth
#             , f"{node.Heuristic:.4f}"
#             , actionlist
#         ))
#     return result
# print(displayFull(possibleStates))

# # print(possibleStates[0].NodeEngine.GameState.Units.UnitHps[:4])
# distinctHps = dict()
# for node in possibleStates:
    # hps = tuple(node.NodeEngine.GameState.Units.UnitHps[:4])
    # if hps in distinctHps:
    #     distinctHps[hps] += 1
    # else:
    #     distinctHps[hps] = 1
# print(distinctHps)

#MANUAL ACTION APPLICATION
# myEngine.useHelperArraysLocs = False
# myEngine.Initialization()
# print(myEngine.GameState)
# print(myEngine.availableActions[10])
# print(myEngine.getAvailableMoves(0, (0, 0, 1), 9))
# print("Prior moves", myEngine.getAvailableMoves(1, (0, 1, 1), 9))
# print(myEngine.availableActions)
# myEngine.applyAction(myEngine.availableActions[10])
# print("After moves", myEngine.getAvailableMoves(0, (0, 0, 1), 9))
# myEngine.applyAction([1, 24, 255, 1,   0, 1, 1,   0, 1, 1])
# print(myEngine.availableActions)
# print(myEngine.GameState)

# for x, col in enumerate(myEngine.GameState.Map):
#     for y, terrainnum in enumerate(col):
#         print(x, y, myEngine.getLocZoc(x, y, 1), myEngine.locZoc[(x, y, 1)])

#endregion run manually


#This is like a stress test on the code
# Player1 = clsPlayerRandom()
# Player2 = clsPlayerRandom()
# myGameManager = clsGameManager()
# write_constants_file(myGameManager.GameData) #don't need to run this every time, could put it in a utility packet
# myGameManager.setMap(mapFilename="plainsLine", playerListInstance=[Player1, Player2])
# myGameManager.play(gameCount=100)



#ok now let's do:
#ADD ACTION COUNTING IN CURRENT METADATA
#selection of action from deep search using criteria
    #curated list
    #present list in visualizer for user
#utility - combat chains. Probability of death from any sequence of attacks from units of various hps and terrain etc
    #enter in separate utility or quick make map and run single turn on enemy with goal of killing unit, calc prob of success?
#game logging for replays and ai training and whatnot
#see if we can get a CPU of any kind of solve tank vs plasma or something similar, or even the 10 vs 1 for that matter.
#   two marines on swamp with a mountain in between
#automatically detect changes to player files and increment their version?
#a player that is local to unit - just checking if it can be killed (within reason?) or just tries to get best value
#unhandled stuff: 
#   underlings underground
#   submersibles
#   conversion
#   emp
#   teleport
#   uv
#   salamander plague passive
#   infector plague active
#   base/harbor capture
#   build units 

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
    #clsEngine
        #GameData
        #GameState
#we could make the engine reference the GameManager
#but I do like the ability to use clsEngine all on it's own.

