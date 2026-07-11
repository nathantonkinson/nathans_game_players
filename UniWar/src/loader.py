#converts files to cleansed: game state, maps, mods, and AIs
#data classes elsewhere

import csv
import yaml
from pathlib import Path
from dataclasses import dataclass, is_dataclass, fields
import numpy as np
from typing import get_origin, get_args, Union
from numpy.typing import NDArray

#my project imports
from src.gameDataClasses import GameData, GameState

#get root directory of uniwar
mydir = Path(__file__).resolve().parent #we assume loader is in src/ and gameData is in the root of the project, so we can use BASE_DIR to get to it
root_dir = mydir.parent

#we could put the data classes in here instead of engine

class Loader:
    def __init__(self):
        #does not have to be in the init
        self.gameData_dir = root_dir / "gameData" #game data is at UniWar/gameData
        self.maps_dir = root_dir / "maps" #maps are at UniWar/maps

    def load_csv(self, file_path):
        with open(file_path, newline='') as f:
            
            # #MANUAL METHOD
            # # Try comma first
            # reader = csv.DictReader(f, delimiter=",")
            # rows = list(reader)
            # # If only one key, probably wrong delimiter
            # if len(rows) > 0 and len(rows[0].keys()) == 1:
            #     f.seek(0)
            #     reader = csv.DictReader(f, delimiter="\t")
            #     rows = list(reader)

            #AUTOMATIC detect dialect. Get sample then try
            sample = f.read(1024)                 # read a small chunk
            f.seek(0)                             # rewind
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
                # dialect = csv.Sniffer().sniff(sample) # auto-detect delimiter, doesn't work on too small of sample
            except csv.Error:
                # Fallback to comma if detection fails
                dialect = csv.get_dialect("excel")

            #read it all
            readerResult = csv.DictReader(f, dialect=dialect)

            return list(readerResult) #a list of identically structured dicts

    def load_yaml(self, file_path):
        with open(file_path) as f:
            return yaml.safe_load(f)

    def load_gameData(self) -> GameData:
        
        #for each data table
        #for each row in the data table
        #call from_dict
        myGameData = GameData()

        for f in fields(myGameData):
            #check target class is list of dataclass
            origin = get_origin(f.type)
            if origin is not list: raise RuntimeError(f"GameData {f.name} is not a list")
            element_type = get_args(f.type)[0]
            if not is_dataclass(element_type): raise RuntimeError(f"GameData {f.name} should be a list of dataclass")

            #file load as list of identically structured dicts
            csv_path = self.gameData_dir / f"{f.name}.csv"
            if not csv_path.exists(): raise RuntimeError(f"{csv_path} does not exist")
            dictlist = self.load_csv(self.gameData_dir / f"{f.name}.csv")

            #load
            loadlist = [self.from_dict(element_type, row) for row in dictlist]
            object.__setattr__(myGameData, f.name, loadlist)
        
        return myGameData
            
    def from_dict(self, cls, data):
        #takes in data in the form of dictionaries and lists (nested)
        #loads into classes with identically named properties

        if not is_dataclass(cls):
            return data

        kwargs = {}

        def is_ndarray_type(t):

            # f.type is np.ndarray or (get_origin(f.type) is Union and np.ndarray in get_args(f.type))
            # print(f.type)

            # Case 1: direct np.ndarray
            if t is np.ndarray:
                # print("Is ndarray")
                return True

            # Case 2: NDArray[...] typing alias
            if get_origin(t) is np.ndarray:
                # print("Is NDArray")
                return True

            # Case 3: Optional[NDArray[...]]
            origin = get_origin(t)
            if origin is Union:
                # print("Origin is union")
                return any(is_ndarray_type(arg) for arg in get_args(t))
            
            # print("Not caught type")

        #If we wanted to read from NDArray[np.unit8] rather than from metadata
        # def get_ndarray_dtype(t):
        #     """Return dtype if t is NDArray[dtype], else None."""
        #     origin = get_origin(t)
        #     if origin is np.ndarray:
        #         args = get_args(t)
        #         if len(args) == 2:
        #             return args[1]  # numpy.dtype(np.uint8)
        #     return None

        for f in fields(cls):
            value = data.get(f.name)

            # print(f.name, f.type, value)

            # Nested single dataclass
            if is_dataclass(f.type):
                kwargs[f.name] = self.from_dict(f.type, value)

            # List of dataclasses
            elif (getattr(f.type, "__origin__", None) is list and is_dataclass(f.type.__args__[0])):
                inner = f.type.__args__[0]
                kwargs[f.name] = [self.from_dict(inner, v) for v in value]

            #optional field actually missing I think
            elif value is None:
                kwargs[f.name] = None
            
            # NumPy array - so do array conversion. Fancy union stuff to catch optional type fields
            elif is_ndarray_type(f.type):
                dtype = f.metadata.get("dtype", None)
                kwargs[f.name] = np.array(value, dtype=dtype)

            # Normal field
            else:
                kwargs[f.name] = value

        return cls(**kwargs)
    
    def load_map(self, mapFilename):
        path = self.maps_dir / mapFilename
        raw = self.load_yaml(path) #loads data as dicts and stuff
        myMap: GameState = self.from_dict(GameState, raw)
        # return raw
        return myMap
