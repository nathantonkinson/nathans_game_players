import random

from src.engine.playerParent import playerParent

class clsPlayerRandom(playerParent):
    def __init__(self, **kwargs): #no required arguments, put optional arguments between self and **kwargs
        super().__init__(**kwargs) #runs the init of template/parent
        #overrides of default properties
        self.description = "Picks a random action from availabeActions"
        self.author = "Nathan Tonkinson"

    def choose_action(self):
        #Return a clsAction. Child classes override this.
        #Use the self.engine as data on the current state
        idx = random.randrange(len(self.engine.availableActions))
        chosenAction = self.engine.availableActions[idx]
        return chosenAction