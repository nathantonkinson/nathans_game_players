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
from src.engine.engine import clsEngine
from src.engine.playerParent import playerParent
import src.data.generated_constants as gc
import src.errorHandler as eh


TIMELIMIT_SECONDS_DEFAULT = 60

#currently we're only handling one map, but later we'll expand to handle:
#   tournaments (ordered lists of maps, explicit player pools, conditions for retrieving player pool)
#   elo determination (select maps or conditions for map pool, conditions for player pool, some kind of balanced matchup, incremental or from fresh elo)
class clsGameManager:
    def __init__(self
            , inputGameData: clsGameData = None
            ):

        self.Loader = Loader()
        
        #game data, state, and engine. Do not have self.GameData, keep it in the engine for copy/reference purposes
        #game data
        if inputGameData is None:
            self.GameData: clsGameData = self.Loader.load_GameData()
            self.GameData = f.allFlattening(self.GameData)

        #just so ide recognizes them or something
        self.GameState = None
        self.GameStateStart = None
        self.players = None
        self.timelimit_seconds = TIMELIMIT_SECONDS_DEFAULT
        
    #one map with it's players. Could play multiple times on same map in different mirrors
    #load map, load players, map hashtag handling
    def setMap(self
            , mapFilename: str = None
            , mapState: clsGameState = None
            , playerListInstance: list[playerParent] = None
            , playerListClass: list[playerParent] = None
            , playerListFilename: list[str] = None
            ):

        #map/state
        if mapState is None:
            mapState: clsGameState = self.Loader.load_map(mapFilename)
        elif mapFilename is None:
            eh.error("No map provided")
        mapState = stateCleanse(mapState, self.GameData) 
        self.GameStateStart: clsGameState = mapState
        self.GameState: clsGameState = copy.deepcopy(self.GameStateStart)
        eh.warning("Switch gamemanager to use clone_engine instead of deepcopy")

        #players instances get
        # players_dir = Path("./players")
        self.players = []
        if playerListInstance is None and playerListClass is None and playerListFilename is None:
            eh.error("No players provided")
        #prioritize the instance list, so if missing load them
        if playerListInstance is None:
            if playerListClass is None:
                for filename in playerListFilename:
                    module_name = Path(filename).stem
                    module_path = f"players.{module_name}" #players folder must be in project root so that import it looks like "import players.myplayer" whatever
                    module = importlib.import_module(module_path)
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, playerParent) and obj is not playerParent:
                            playerListClass.append(obj)
            #initialize the classes
            for obj in playerListClass:
                playerListInstance.append(obj()) #they should not need arguments in their initialization
        #correct number of players?
        if len(playerListInstance) != len(self.GameState.MetadataInitial.PlayersInitial):
            eh.error("Number of players provided for this map is incorrect")
        self.players = playerListInstance

        #hashtag handling
        self.timelimit_seconds: str = next(
            (s for s in self.GameState.MetadataInitial.Hashtags if s.startswith("BLITZACTION"))
            , TIMELIMIT_SECONDS_DEFAULT)
            #though really, a CPU can/should decide all moves at the same time, not action by action, but whatever

        #get the number of teams for no good reason
        self.teams_count = 0
        for p, player in enumerate(self.GameState.MetadataInitial.PlayersInitial):
            if player.Team > self.teams_count: self.teams_count = player.Team
        self.teams_count += 1 #final to be a count instead of max index

        #throw errors for player configs incompatible with map
        #required and excluded hashtags
        eh.warning("Not yet checking for players hashtag settings incompatible with map")

    def gameStart(self):
        #stuff that should run once at the beginning of each individual game

        #engine (holds GameState and GameData)
        self.Engine: clsEngine = clsEngine(self.GameState, self.GameData) #the engine does replace GameData when it handles some hashtags (no healing)... ugh
        self.Engine.GameState = copy.deepcopy(self.GameStateStart)
        eh.warning("Switch gamemanager to use clone_engine instead of deepcopy")
        self.Engine.Initialization()

        #reset the players
        #set the player engine, indexes, and timeouts, races
        #do races. If map is variable race, use player preferred (if exists) or random. Convert map units to type. 
        self.players = [p.__class__() for p in self.players] #re-initialize all the players. Will break other references
        for p, player in enumerate(self.players):
            player.playerIndex = p
            player.timelimit_seconds = self.timelimit_seconds
            player.engine = self.Engine
            initialRace = self.Engine.GameState.MetadataInitial.PlayersInitial[p].Race
            if initialRace == 0:
                self.Engine.GameState.MetadataInitial.PlayersInitial[p].Race = player.choose_race() #we could have the player set it internally but I'd rather we control that
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
        #returns winning team, or None for tie
        #or can just set the winning team property and return

        replay = []

        self.gameStart()

        while self.Engine.GameState.MetadataCurrent.WinnerTeam is None:
            round = self.Engine.GameState.MetadataCurrent.CurrentRound
            cp = self.Engine.GameState.MetadataCurrent.CurrentPlayer
            currentPlayerInstance = self.players[cp]
            action = currentPlayerInstance.choose_action_withtimelimit()
            if currentPlayerInstance.timedout == True: 
                #forfeits the game
                eh.error("A player timed out")
                break

            availableActionCount = len(self.Engine.availableActions)
            print(f"Round {round}, player {cp}, actions available count={availableActionCount}")
            actions_abbrev = [a.AbilityNumber for a in self.Engine.availableActions]
            print(f"Action abilities available: {actions_abbrev}")
            print(f"Applying action: {action}")
            self.Engine.applyAction(action)
            # input("Press Enter to continue...")
        
        #determine winner and return
        if self.Engine.GameState.MetadataCurrent.WinnerTeam is None: #no winner, use tournament tie-breaking
            #we also have wincon stuff in the engine, but this is tournament tie-breaking wincon stuff that only occurs once game is done
            #we will use what I see as standard from miamimoose, at round limit winner is most bases > most kills > draw
            team_bases = [0]*self.teams_count
            for x, col in enumerate(self.GameState.Map):
                for y, terrainNum in enumerate(col):
                    if terrainNum in (15): #base (we are not including harbors=2)
                        p = self.Engine.locPlayers[(x, y)]
                        if p not in [-1, 255, None]:
                            t = self.GameState.MetadataInitial.PlayersInitial[p].Team
                            team_bases[t] += 1
            #find team with most bases or tie
            max_bases = max(team_bases)
            max_teams = [t for t, n in enumerate(team_bases) if n == max_bases]
            if len(max_teams) == 1:
                self.GameState.MetadataCurrent.WinnerTeam = max_teams[0]
        if self.GameState.MetadataCurrent.WinnerTeam is None: #no base tiebreaking, use kills
            team_killvalue = [0]*self.teams_count
            for p, player in enumerate(self.GameState.MetadataCurrent.PlayersKills):
                pass
        

        #got a winning team now (or none)
        if self.GameState.MetadataCurrent.WinnerTeam is not None:
            winningPlayers = [] 
            for p, player in enumerate(self.Engine.GameState.MetadataInitial.PlayersInitial):
                if player.Team == self.GameState.MetadataCurrent.WinnerTeam:
                    winningPlayers.append(self.players[p].name)
            eh.info(f"Winner is team #{self.GameState.MetadataCurrent.WinnerTeam}, players={winningPlayers}")
            return self.GameState.MetadataCurrent.WinnerTeam
        else: #tie
            return -1


    def play(self, doMirror: bool = False, gameCount: int = 1):

        for _ in range(gameCount):
            print("NEW GAME STARTING")
            self.playOne() #reset is used in playOne


