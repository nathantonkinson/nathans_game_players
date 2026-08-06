from src.engine.playerParent import playerParent

class clsPlayerFirstchoice(playerParent):
    def __init__(self, **kwargs): #no required arguments, put optional arguments between self and **kwargs
        super().__init__(**kwargs) #runs the init of template/parent
        #overrides of default properties
        self.description = "Picks first action from available actions"
        self.author = "Nathan Tonkinson"

    def choose_action(self):
        #Return a clsAction. Child classes override this.
        #Use the self.engine as data on the current state
        chosenAction = self.engine.availableActions[0]
        return chosenAction