#add default python imports here (dataclasses, numpy, etc)

#you will need to do your own imports from the repo here
from players._playerTemplate import playerTemplate
from src.data.gameDataClasses import GameData, GameState, clsAction

class myPlayer(playerTemplate):
    def __init__(self): #no required arguments, optional args ok
        super().__init__() #runs the init of template/parent

        #optional overrides of metadata already initialized with placeholders from the parent
        self.description = "(No description)"
        self.author = "(No author given)" #this should be uniwar username
        self.version = "(No version given)" #useful perhaps if we are doing genetic algorithms or something...

        #do your own init stuff here

    def choose_action(self) -> clsAction:
        #Return a clsAction. Child classes override this.
        #Use the self.engine as data on the current state
        raise NotImplementedError("Child AI must implement choose_action()")