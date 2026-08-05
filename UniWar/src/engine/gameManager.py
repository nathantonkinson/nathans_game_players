#takes in map path, players
#sets up it's own engine if needed
#loads it's own gamedata if needed
#runs the players against each other until a win
#generates logs

import os
import importlib
import inspect
from pathlib import Path
import copy

from src.data.loader import Loader
import src.data.flattening as f
from src.data.stateCleanse import stateCleanse
from src.data.gameDataClasses import clsGameState, clsGameData
from src.engine.engine import Engine
from players._playerTemplate import playerTemplate
import src.data.generated_constants as gc



class clsGameManager:
    def __init__(self
            , mapFilename: str = None
            , mapState: clsGameState = None
            , inputGameData: clsGameData = None
            , playerListInstance: list[playerTemplate] = None
            , playerListClass: list[playerTemplate] = None
            , playerListFilename: list[str] = None
            ):

        myLoader = Loader()

        #game data, state, and engine. Do not have self.GameData, keep it in the engine for copy/reference purposes
        #game data
        if inputGameData is None:
            inputGameData: clsGameData = myLoader.load_GameData()
            inputGameData = f.allFlattening(inputGameData)
        #map/state
        if mapState is None:
            mapState: clsGameState = myLoader.load_map(mapFilename)
        elif mapFilename is None:
            raise RuntimeError("No map provided")
        mapState = stateCleanse(mapState, inputGameData) 
        self.GameStateStart: clsGameState = copy.deepcopy(mapState)
        #engine (holds GameState and GameData)
        self.Engine: Engine = Engine(mapState, inputGameData)

        #players instances get
        # players_dir = Path("./players")
        self.players = []
        if playerListInstance is None and playerListClass is None and playerListFilename is None:
            raise RuntimeError("No players provided")
        #prioritize the instance list, so if missing load them
        if playerListInstance is None:
            if playerListClass is None:
                for filename in playerListFilename:
                    module_name = Path(filename).stem
                    module_path = f"players.{module_name}" #players folder must be in project root so that import it looks like "import players.myplayer" whatever
                    module = importlib.import_module(module_path)
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, playerTemplate) and obj is not playerTemplate:
                            playerListClass.append(obj)
            #initialize the classes
            for obj in playerListClass:
                playerListInstance.append(obj()) #they should not need arguments in their initialization
        #correct number of players?
        if len(playerListInstance) != len(self.Engine.GameState.MetadataInitial.PlayersInitial):
            raise RuntimeError("Number of players provided for this map is incorrect")
        self.players = playerListInstance

        #hashtag handling
        self.timelimit_seconds: str = next((s for s in self.Engine.GameState.MetadataInitial.Hashtags if s.startswith("BLITZACTION")), 60)
            #though really, a CPU should decide all moves at the same time, not action by action, but whatever

        #throw errors for player configs incompatible with map
        #if map has required races, players must be able to play those (in order)
        #required and excluded hashtags

    def gameStart(self):
        #stuff that should run once at the beginning of each individual game

        self.Engine.GameState = copy.deepcopy(self.GameStateStart)
        self.Engine.Initialization()

        #set the player engine, indexes, and timeouts, races
        #do races. If map is variable race, use player preferred (if exists) or random. Convert map units to type. 
        self.players = [p.__class__() for p in self.players] #re-initialize all the players. Will break other references

        for p, player in enumerate(self.players):
            player.playerIndex = p
            player.timelimit_seconds = self.timelimit_seconds
            player.engine = self.Engine
            initialRace = self.Engine.GameState.MetadataInitial.PlayersInitial[p].Race
            if initialRace == 0:
                player.race = player.choose_race() #we could have the player set it internally but I'd rather we control that
            else:
                player.race = initialRace
            #convert all generic units owned by this player to the race
            for ur, unitnum in enumerate(self.Engine.GameState.Units.UnitNumbers):
                if unitnum in [0, -1, 255, None]: continue
                unit_race = self.Engine.GameData.Units[(unitnum, gc.RACENUMBER)]
                if unit_race == 0: #is generic, need to convert
                    role_num = self.Engine.GameData.Units[(unitnum, gc.UNITROLENUMBER)]
                    for u, unit in self.Engine.GameData.Units:
                        if unit[gc.RACENUMBER] == player.race and unit[gc.UNITROLENUMBER] == role_num:
                            self.Engine.GameState.Units.UnitNumbers[ur] = u

    def playOne(self):
        #plays the players against each other until someone wins

        replay = []

        self.gameStart()

        while self.Engine.GameState.MetadataCurrent.WinnerTeam is None:
            round = self.Engine.GameState.MetadataCurrent.Round
            cp = self.Engine.GameState.MetadataCurrent.CurrentPlayer
            currentPlayerInstance = self.players[cp]
            action = currentPlayerInstance.choose_action_withtimelimit()
            if currentPlayerInstance.timedout == True: 
                #forfeits the game
                raise RuntimeError("A player timed out")
                break

            availableActionCount = len(self.Engine.availableActions)
            print(f"Round {round}, player {cp}, actions available count={availableActionCount}")
            actions_abbrev = [a.AbilityNumber for a in self.Engine.availableActions]
            print(f"Action abilities available: {actions_abbrev}")
            print(f"Applying action: {action}")
            self.Engine.applyAction(action)
            # input("Press Enter to continue...")

        winningTeam = self.Engine.GameState.MetadataCurrent.WinnerTeam
        winningPlayers = []
        if winningTeam is not None:
            for p, player in enumerate(self.Engine.GameState.MetadataInitial.PlayersInitial):
                if player.Team == winningTeam:
                    winningPlayers.append(self.players[p].name)
        else:
            winningPlayers = ["A tie or some kind of failure"]
        print(f"Winner is team #{winningTeam}, players={winningPlayers}")

    def play(self, doMirror: bool = False, gameCount: int = 1):

        for _ in range(gameCount):
            print("NEW GAME STARTING")
            self.playOne() #reset is used in playOne


