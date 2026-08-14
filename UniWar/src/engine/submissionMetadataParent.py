import sys
from pathlib import Path

from src.engine.engine import clsEngine

class clsSubmissionMetadataParent():
    def __init__(self):

        #metadata
        #filename shennanigans
        module = sys.modules[self.__class__.__module__]
        # self.filepath = module.__file__
        # self.filenamewithmod = self.__class__.__module__ #this will get you "players.[filename]"
        # self.filename = os.path.basename(module.__file__)
        path = Path(module.__file__)
        self.filepath = str(path)
        self.filestem = path.stem #MyPlayer"
        # self.filename = path.name   # "MyPlayer.py"
        self.name = self.filestem #used for display, differenatiation of multiple instances of same player class, I will edit name from outside
        self.description = f"(No description)" #could do f"{self.filestem} (no description)""
        self.author = "(No author given)" #this should be uniwar username
        self.version = "(No version given)" #useful perhaps if we are doing genetic algorithms or something... 
            #ugh I want players without init arguments but if I want a generic player that takes in a kind of neural net of which there are many variants... ugh
        
        #context allowed
        self.allowedRaces = {1, 2, 3} #will exclude this player from games that require them to be a player not in this list
        self.preferredRaces = {} #if given the choice, will pick randomly from this list
        self.excludedHashtags = {"RNGBUILD", "RNGBUILDANY", "EDITSTATS"}
        self.requiredHashtags = {} #if limited player, things like #NOREPAIR or something that limits to one unit type
        self.allowedMaps = {} #leave empty for any map. Can use step or with extension. I expect you'd exclude maps via hashtags. I expect players to either be general or basically only good for 1 map.

        #timeout
        self.timedout = False #is set to true if your choose_action does not return within the time allotted, the game manager will detect this and make you forfeit.
        self.timelimit_seconds = 60 #I guess we're defaulting to 1 minute per action if game manager doesn't set it for us

        #information used for calcs, will be assigned by caller
        self.engine: clsEngine = None