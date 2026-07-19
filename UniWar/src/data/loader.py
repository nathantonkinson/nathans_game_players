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
import src.data.gameDataClasses as dc
from src.data.gameDataClasses import GameData, GameState


#get root directory of uniwar
mydir = Path(__file__).resolve().parent #we assume loader is in src/data/ and gameData is in the root of the project, so we can use BASE_DIR to get to it
root_dir = mydir.parent.parent

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

    def coerce(self, value, dtype):
        #coerces values to np dtype, None for failures

        dt = np.dtype(dtype)

        # Special case: string to booleans
        if dt == np.bool_ and type(value) == str:
            s = str(value).strip().lower()
            if s in ("1", "true", "t", "yes", "y"):
                return True
            if s in ("0", "false", "f", "no", "n", ""):
                return False
            return None
    
        # Special case: string to int
        if dt == np.uint8 and type(value) == str: #idk why but uint (rather than int) doesn't work with ""
            s = str(value).strip().lower()
            if s in (""):
                return 0

        # Generic NumPy coercion
        try:
            return dt.type(value)
        except Exception:
            return None

    def from_dict(self, cls, data):
        #takes in data in the form of dictionaries and lists (nested)
        #loads into nested data classes with identically named properties that have numpy arrays at the bottom, or sometimes numpy string or numpy uint or python string or python int
        #currently does not handle a cls that is not a dataclass (e.g. a list, dictionary or whatever else)

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

    def load_gameDataOld(self) -> GameData: #loads as lists of dataclasses, not ideal
        
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

    def load_GameData(self) -> GameData: #loads each csv as a numpy, then each numpy into the gamedata initializer

        #we could use int16 for everything to make uniform, but being specific will probably help
        #idk how to do dtypes per packed column, probably can't
        fields = {} #destination

        #LOOP
        for loadtable in dc.gamedata_raw_structure:
            dictlist = self.load_csv(self.gameData_dir / f"{loadtable['name']}.csv")
            
            #solo cols
            maxes = [0]*len(loadtable["solo_cols"]) #not doing min since negative indexes go from other end (can't do negatives for real)
            for c, col in enumerate(loadtable["solo_cols"]):
                for dict in dictlist:
                    x = int(dict[col])
                    if x > maxes[c]: maxes[c] = x
                maxes[c] += 1 #because arrays indexed at 0
            #initialize np array
            shape = tuple(maxes) + (len(loadtable["packed_cols"]),)
            #even if only one packed col we'll make a dim for it, just for consistency
                # if len(loadtable["packed_cols"]) > 1: shape += (len(loadtable["packed_cols"]),)
            out = np.zeros(shape, dtype=loadtable["dtype"])
            #load array
            for dict in dictlist:
                index_solo = tuple(int(dict[col]) for col in loadtable["solo_cols"])
                for c, col in enumerate(loadtable["packed_cols"]):
                    try:
                        out[index_solo + (c,)] = self.coerce(dict[col], loadtable["dtype"]) 
                    except:
                        # print(dict[col]) #blank
                        print(loadtable['name'], index_solo + (c,), col, "dc" + dict[col], loadtable["dtype"])
                        print(type(dict[col]))
                        print(len(dict[col]))
                        raise RuntimeError("hey")
            out.flags.writeable = False
            fields[loadtable["name"]] = out
        
        return GameData(**fields)
        # return fields
 
    def load_map(self, mapFilename):
        path = self.maps_dir / mapFilename
        raw = self.load_yaml(path) #loads data as dicts and stuff
        myMap: GameState = self.from_dict(GameState, raw)
        # return raw
        return myMap
