#proportion of credits I have vs next best enemy team
#credits are unithp*unitvalue + stored credits
#prop=(mine - best opponent)/(mine+best opponent), which varies -1 to 1, so rescale 0 to 1
#assumes NOFOW, though as a human it's pretty easy to get close to this with base information and our kills and guesses about their healing



#you will need to do your own imports from the repo here
from src.engine.heuristicParent import heuristicParent
from src.data.gameDataClasses import clsGameData, clsGameState
from src.engine.engine import clsEngine
import src.data.generated_constants as gc

class creditProp(heuristicParent):
    def __init__(self): #no required arguments, optional args ok
        super().__init__() #runs the init of template/parent

        #optional overrides of metadata already initialized with placeholders from the parent
        self.description = "Proportion of credits vs best opponent team ([hp*val]+player credits)"
        self.author = "Nathan Tonkinson" #this should be uniwar username
        self.version = "1" #useful perhaps if we are doing genetic algorithms or something...

        #other init?? none I think
        self.onlyCurrentPlayer = False #because other players have acted, they will have better scores at that time, but close enough.

    #this is the override of parent
    def getWinProbability(self, engine = None, team_index = None):

        if engine is not None: self.engine = engine

        #some info
        cp = self.engine.GameState.MetadataCurrent.CurrentPlayer
        ct = self.engine.GameState.MetadataInitial.PlayersInitial[cp].Team
        #team argument
        if team_index == None and self.teamIndex == None: 
            self.teamIndex = ct
        if team_index is not None:
            self.teamIndex = team_index
        #count the teams (assumes cleansed state), continuous increase in teams
        team_count = 0
        for p, player in enumerate(self.engine.GameState.MetadataInitial.PlayersInitial):
            if player.Team > team_count: team_count = player.Team
        team_count += 1
        team_credits = [0]*team_count

        #credits in hand
        for p, player in enumerate(self.engine.GameState.MetadataInitial.PlayersInitial):
            t = player.Team
            team_credits[t] += self.engine.GameState.MetadataCurrent.PlayersCredits[p]

        #units
        for u, un in enumerate(self.engine.GameState.Units.UnitNumbers):
            p = self.engine.GameState.Units.UnitPlayers[u]
            if p in [-1, 255, None]: continue
            t = self.engine.GameState.MetadataInitial.PlayersInitial[p].Team
            val = self.engine.GameData.Units[(un, gc.COST)]
            hp = self.engine.GameState.Units.UnitHps[u]
            team_credits[t] += int(val)*int(hp)/10 #will automatically capture veterancy

        #do the math
        my_credits = team_credits[self.teamIndex]
        #find next best team credits after us
        best_opponent_credits = max(c for t, c in enumerate(team_credits) if t != self.teamIndex)
        #0 to 1 proportion
        if my_credits == 0 and best_opponent_credits == 0: #to handle divide by zero
            prop = 0.5
        else:
            prop = 0.5 + (my_credits - best_opponent_credits)/(2*(my_credits + best_opponent_credits)) #-1 to 1 cut in half
            
        return prop