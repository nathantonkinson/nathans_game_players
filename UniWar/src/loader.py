#converts files to cleansed: game state, maps, mods, and AIs
#data classes elsewhere

import csv
import yaml
from pathlib import Path
from dataclasses import dataclass
from src.engine import GameState

mydir = Path(__file__).resolve().parent #we assume loader is in src/ and gameData is in the root of the project, so we can use BASE_DIR to get to it
root_dir = mydir.parent

@dataclass
class Loader:
    def __init__(self):
        #does not have to be in the init
        self.gameData_dir = root_dir / "gameData" #game data is at UniWar/gameData
        self.maps_dir = root_dir / "maps" #maps are at UniWar/maps

    def load_csv(self, file_path):
        with open(file_path) as f:
            return list(csv.DictReader(f))

    def load_yaml(self, file_path):
        with open(file_path) as f:
            return yaml.safe_load(f)

    def load_gameData(self):
        return {
            "terrain": self.load_csv(self.gameData_dir / "terrains.csv")
            , "states": self.load_csv(self.gameData_dir / "states.csv") #units can be in different states in terrain. surface or underground
            , "terrainStates": self.load_csv(self.gameData_dir / "terrainStates.csv")
            , "races": self.load_csv(self.gameData_dir / "races.csv")
            , "unittypes": self.load_csv(self.gameData_dir / "unittypes.csv")
            , "abilities": self.load_csv(self.gameData_dir / "abilities.csv")
            , "units": self.load_csv(self.gameData_dir / "units.csv")
            , "unittypeTerrains": self.load_csv(self.gameData_dir / "unittypeTerrains.csv")
            , "unitTerrains": self.load_csv(self.gameData_dir / "unitTerrains.csv")
            , "unitStates": self.load_csv(self.gameData_dir / "unitStates.csv")
            , "unitUnittypeStates": self.load_csv(self.gameData_dir / "unitUnittypeStates.csv")
            , "unitAbilities": self.load_csv(self.gameData_dir / "unitAbilities.csv")
        }

    def load_map(self, mapFilename):
        path = self.maps_dir / mapFilename
        mapdata = self.load_yaml(path)
        myGameState = GameState()
        myGameState.metatataInitial = mapdata["MetadataInitial"]
        myGameState.map = mapdata["Map"]
        myGameState.metadataCurrent = mapdata["MetadataCurrent"]
        #we might want to put cleansing in here, meaning add the duplicate unitTiles vs tileUnits
        #would we also want to do validation? I think not
        return myGameState
