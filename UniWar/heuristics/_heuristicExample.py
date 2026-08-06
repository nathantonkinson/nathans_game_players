#add default python imports here (dataclasses, numpy, etc)

#you will need to do your own imports from the repo here
from src.engine.heuristicParent import heuristicParent
from src.data.gameDataClasses import GameData, GameState

class heuristicExample(heuristicParent):
    def __init__(self): #no required arguments, optional args ok
        super().__init__() #runs the init of template/parent

        #optional overrides of metadata already initialized with placeholders from the parent
        self.description = "(No description)"
        self.author = "(No author given)" #this should be uniwar username
        self.version = "(No version given)" #useful perhaps if we are doing genetic algorithms or something...

        #do your own init stuff here

    #this is your override of the parent def
    def getWinProbability(self):
        return 0.5