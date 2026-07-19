
from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray
from typing import Optional, List, Protocol
from enum import IntEnum
import sys
import os

#region FLATTEN STRAT

#we will only pass the minimal information required to the neural net, and in the form of 1D arrays
    #this is GameState.Units and GameState.MetadataCurrent
#engine can (not required) to maintain some other info for it's own effeciency
    #see engine for details

#POTENTIAL GAMEDATA FLATTENING for optimization of engine (not net)
    #FLATTEN OPS
        #DONE adding to unitTerrains from unittypeTerrains, making the latter obsolete
        #flattened UnitUnittypeAltitudes by listing each unit from the unittype... meh
        # use the default logic to add an actions [] list to each unit
            #actions per unit is currently in Units but could be in abilities instead. Visa versa with some abilities
            #do passives? probably yes
        #more? primary load is AI, not engine, but nice to optimize engine too
    #USE CASE LOOKUPS, separated
        #ACT: ability list: unitAbilities flattened into a units field as an array
            #needs to be modified if emp... otherwise fine?
        #MOV: 
        #   mobility: unitAltitudes
        #   movement allowed: terrainAltitudes
        #   cost: unittypeTerrains flattened added into unitTerrains
        #   ?? does vision matter?
        #ATK: 
        #   atk range: unitAltitudes
        #   atk base: unitUnittypeAltitude, maybe flattened into unitUnit(defender)Altitude
        #   terrain bonus (both): unittypeTerrains flattened added into unitTerrains
        #   altitude bonus: Altitudes (for submerged)
        #   defense base: unitAltitudes
    #USE CASE VERY FLAT
        #ACT: ability list: unitAbilities flattened into a units field as an array
            #shape: U, A, 3 (exists, cooldown, strength)
        #MOV:
            #one-time retrievals
                #unit number, unit type
                #altitude
                #mobility: unitAltitudes
            #****ZOC: (does unit exist here), hexUnits
            #****movement cost: (one table) combination of unittypeTerrains>unitTerrains (cost), terrainAltitudes (allowed)
                #unit 
                #***terrain - this requires lookup on map, but map static hopefully helps
                #altitude (doesn't exist or cost = 100 or something = not allowed)
        #ATK
            #one-time retrievals
                #unit type
                #unit number
                #altitude (atk penalty submerged)
                #rangemin and max (from unitAltitudes)
            #frequent lookup (one table - gets a p-value)
                #attacker unit number
                #***defending unit type (or unit)
                #***defending altitude
                #attacking unit terrain
                #***defending unit terrain

    #Remaining tables:
        #Units (repair rate, actions/turn) 
        #UnitAbilities (hm... may want this separate because cooldown and strength are separate)
            #Abilities (some of it should be hardcoded, the rest (defaults) flattened into Units)
        #Altitudes (for submerged penalty)
        #TerrainAltitudes (movement allowed)
        #UnitAltitudes (mobility, defense base, atk range)
        #UnitTerrains (atk/def bonus, mobility cost)
            #UnittypeTerrains
        #UnitUnitAltitudes (not a base table, used for atk base)
            #UnitUnittypeAltitudes
        
        #UNUSED
            #Maptags (names only / hardcoded)
            #Races (names only)
            #Terrains (names only)
            #UnitTypes (names only)
#endregion flatten strat


#region gameState frozen
@dataclass(frozen=True) #once created, cannot be changed, but is now hashable
#we don't need to make the metadata portion super small and fast, since it won't be copied. But doing so anyway for the moment
class GameMetadataInitial:
    MapName:        np.str_
    PlayersInitial: np.ndarray #should be filled with identical dicts with race:, and maybe credits:
    MapDescription: np.str_                     = field(default=None)
    Username:       np.str_                     = field(default=None)
    StartingCredits: np.uint16                  = field(default=0)
    BaseCredits:    np.uint16                   = field(default=100)
    CityCredits:    np.uint16                   = field(default=50)
    Hashtags:       Optional[NDArray[np.str_]]  = field(default_factory=np.ndarray)

    def __post_init__(self):
        # assert self.playersInitial.ndim == 1, how do we check this is filled with dicts or whatever it is?
        pass

#Could do map without dataclass but it might help if it's frozen (does it?)
@dataclass(frozen=True)
class GameMap:
    Map:                NDArray[np.uint8]           = field(metadata={"dtype": np.uint8}) #dimensions set when initialized
    #potenitally could put the unittype movement cost in each tile for faster lookup? since this is immutable
        #would this be faster?
    #units are adjacent to: (-1, 1), (0, 1), (-1, 0), (1, 0), (0, -1), (1, -1)
        #y axis is slanted right into +x+y on normal graph

    
    def __post_init__(self):
        assert self.Map.ndim == 2, "Map should be 2 dimensional (x, y)" #state is for units, terrain types have states built in

#endregion

#region gameState non-frozen
@dataclass
class GameMetadataCurrent:
    PlayersCredits:     NDArray[np.uint16]          = field(metadata={"dtype": np.uint16})
    CurrentPlayer:      np.uint8                    = field(default=0, metadata={"dtype": np.uint8}) #starts at 0
    WinnerPlayer:       np.uint8                    = field(default=None, metadata={"dtype": np.uint8})
    def __post_init__(self):
        assert self.PlayersCredits.ndim == 1, "Players credits should be 1 dim array"

@dataclass
class GameUnits:
    UnitPlayers:    NDArray[np.int8]               = field(metadata={"dtype": np.uint8})
    UnitNumbers:    NDArray[np.uint8]               = field(metadata={"dtype": np.uint8}) #capping out at 256 unit types lol
    UnitHps:        NDArray[np.uint8]               = field(metadata={"dtype": np.uint8})
    UnitHexes:      Optional[NDArray[np.uint8]]     = field(default=None, metadata={"dtype": np.uint8}) #shape (U index, 3 (H, W, S))
    #UnitExp
    #some kind of special properties, like cooldowns, plague, emp
    
    #These will be maintained by the engine for it's own efficiency, but not passed to the neural net  
    # HexUnits:       Optional[NDArray[np.uint8]]     = field(default=None, metadata={"dtype": np.uint8}) #shape (H, W, S) with no entries for places without units 
    # UnitDefenses:   Optional[NDArray[np.uint8]]     = field(default=None, metadata={"dtype": np.uint8}) #unit defense + terrain bonus + submerged bonus
    

    def __post_init__(self):
        assert self.UnitPlayers.ndim == 1, "unit numbers must be 1D"
        assert self.UnitNumbers.ndim == 1, "unit numbers must be 1D"
        assert self.UnitHps.ndim == 1, "hp must be 1D"
        if self.UnitHexes is not None:
            assert self.UnitHexes.ndim == 2, "unit tiles must be 2D (unit_index, 3 (x, y, altitude))"
            assert self.UnitHexes.shape[1] == 3, "unit tiles 2nd dimension must be size 3 (for height, width, and state (surface air, underwater, underground))"
        # if self.HexUnits is not None:
        #     assert self.HexUnits.ndim == 3, "tileUnits must be 3D, (x, y, state) = unit index"
        #     assert self.HexUnits.shape[2] == 3, "tileUnits 3rd dim must be size 3 state (surface air, underwater, underground)"

@dataclass
class GameState:
    # def __init__(self): #I think this will be more costly, and/or isn't actually using the dataclass features
    MetadataInitial:    GameMetadataInitial         = field()
    Map:                GameMap
        
    MetadataCurrent:    GameMetadataCurrent
    Units:              GameUnits                   = field()
        #duplicate data under here unitTiles and tilesUnit (or something)
    
#endregion non-frozen

#region old game data (list of dataclasses)
#region dataclass for each table
@dataclass(frozen=True)
class DataAbilities:
    Name:               str
    Number:             int
    RequiresAction:     bool
    AllowMovement:      bool #maybe can be nullable for the ones that don't require action?
    Notes:              str

@dataclass(frozen=True)
class DataAltitudes:
    Name:               str
    Number:             int
    AttackModifier:     int #for -2 underwater and -100 underground (not valid to attack anything from underground, even enemy underground units)

@dataclass(frozen=True)
class DataMaptags: #all hardcoded... do we even want this table? Maybe for visualization...
    Name:               str
    Number:             int
    Notes:              str

@dataclass(frozen=True)
class DataRaces:
    Name:               str
    Number:             int

@dataclass(frozen=True)
class DataTerrainAltitudes:
    TerrainName:        str #can be deduced from #
    TerrainNumber:      int
    AltitudeName:       str #can be deduced from #
    AltitudeNumber:     int
    Allowed:            bool

@dataclass(frozen=True)
class DataTerrains:
    Name:               str
    Number:             int
    Notes:              str

@dataclass(frozen=True)
class DataUnitAbilities:
    UnitName:           str #deduced from #
    UnitNumber:         int
    AbilityName:        str #deduced
    AbilityNumber:      int
    Notes:              str
    Cooldown:           int
    AbilityStrength:    int

@dataclass(frozen=True)
class DataUnitAltitudes:
    UnitRaceName:       str #deduced
    UnitName:           str #deduced
    UnitNumber:         int
    AltitudeName:       str #deduced
    AlttitudeNumber:    int
    Mobility:           int
    Vision:             int
    AttackRangeMin:     int
    AttackRangeMax:     int
    Defense:            int

@dataclass(frozen=True)
class DataUnits:
    RaceName:           str #deduced
    RaceNumber:         int
    Name:               str
    Number:             int
    Cost:               int #nullable for the converted ones
    UnittypeName:       str #deduced
    UnittypeNumber:     int
    Repair:             int
    ActionsPerTurn:     int
    Notes:              str

@dataclass(frozen=True)
class DataUnitTerrains:
    UnitName:           str #deduced
    UnitNumber:         int
    TerrainName:        str #deduced
    TerrainNumber:      int
    MobilityCost:       int
    AttackBonus:        int
    DefenseBonus:       int
    MovementAllowed:    bool
    Notes:              str

@dataclass(frozen=True)
class DataUnittypes:
    Name:               str
    Number:             int
    Notes:              str

@dataclass(frozen=True)
class DataUnittypeTerrains:
    UnittypeName:       str #deduced
    UnittypeNumber:     int
    TerrainName:        str #deduced
    TerrainNumber:      int
    MobilityCost:       int
    AttackBonus:        int
    DefenseBonus:       int
    MovementAllowed:    bool #default yes, if no row then no
    Notes:              str

@dataclass(frozen=True)
class DataUnitUnittypeAltitudes:
    UnitRaceName:           str #deduced
    UnitName:               str
    UnitNumber:             int
    DefenderUnittypeName:   str #deduced
    DefenderUnittypeNumber: int
    DefenderAltitudeName:   str #deduced
    DefenderAltitudeNumber: int
    Strength:               int
    Armorpiercing:          int 

#endregion game data individual tables

# @dataclass(frozen=True)
# class GameData:
#     Abilities:              List[DataAbilities]                 =field(default_factory=list)
#     Altitudes:              List[DataAltitudes]                 =field(default_factory=list)
#     Maptags:                List[DataMaptags]                   =field(default_factory=list)
#     Races:                  List[DataRaces]                     =field(default_factory=list)
#     TerrainAltitudes:       List[DataTerrainAltitudes]          =field(default_factory=list)
#     Terrains:               List[DataTerrains]                  =field(default_factory=list)
#     UnitAbilities:          List[DataUnitAbilities]             =field(default_factory=list)
#     UnitAltitudes:          List[DataUnitAltitudes]             =field(default_factory=list)
#     Units:                  List[DataUnits]                     =field(default_factory=list)
#     UnitTerrains:           List[DataUnitTerrains]              =field(default_factory=list)
#     Unittypes:              List[DataUnittypes]                 =field(default_factory=list)
#     UnittypeTerrains:       List[DataUnittypeTerrains]          =field(default_factory=list)
#     UnitUnittypeAltitudes:  List[DataUnitUnittypeAltitudes]     =field(default_factory=list)

#endregion old game data class (list of dataclasses)

#region np game data indexed

gamedata_raw_structure = [
    {"name": "Abilities", "dtype": np.bool_, "solo_cols":["Number"], "packed_cols": ["RecordExists", "RequiresAction", "Default", "AllowMovement"]}
    , {"name": "Altitudes", "dtype": np.int8, "solo_cols":["Number"], "packed_cols": ["AttackBonus"]}
    , {"name": "Maptags", "dtype": np.str_, "solo_cols":["Number"], "packed_cols":["Name"]} #we have name just so there is some data in here
    , {"name": "Races", "dtype": np.str_, "solo_cols":["Number"], "packed_cols":["Name"]} #we have name just so there is some data in here
    , {"name": "TerrainAltitudes", "dtype": np.bool_, "solo_cols":["TerrainNumber", "AltitudeNumber"], "packed_cols": ["Allowed"]}
    , {"name": "Terrains", "dtype": np.str_, "solo_cols":["Number"], "packed_cols":["Name"]} #we have name just so there is some data in here
    , {"name": "UnitAbilities", "dtype": np.uint8, "solo_cols":["UnitNumber", "AbilityNumber"], "packed_cols": ["RecordExists", "Cooldown", "AbilityStrength"]}
    , {"name": "UnitAltitudes", "dtype": np.int8, "solo_cols":["UnitNumber", "AltitudeNumber"], "packed_cols": ["Mobility", "Vision", "AttackRangeMin", "AttackRangeMax", "Defense"]}
    , {"name": "Units", "dtype": np.uint8, "solo_cols":["Number"], "packed_cols": ["RaceNumber", "Cost", "UnittypeNumber", "Repair", "ActionsPerTurn"]}
    , {"name": "UnitTerrains", "dtype": np.int8, "solo_cols":["UnitNumber", "TerrainNumber"], "packed_cols":[ "AttackBonus", "DefenseBonus", "MovementAllowed", "MobilityCost"]}
    , {"name": "Unittypes", "dtype": np.str_, "solo_cols":["Number"], "packed_cols":["Name"]} #we have name just so there is some data in here
    , {"name": "UnittypeTerrains", "dtype": np.int8, "solo_cols":["UnittypeNumber", "TerrainNumber"], "packed_cols":["AttackBonus", "DefenseBonus", "MovementAllowed", "MobilityCost"]}
    , {"name": "UnitUnittypeAltitudes", "dtype": np.float16, "solo_cols":["UnitNumber", "DefenderUnittypeNumber", "DefenderAltitudeNumber"], "packed_cols":["Strength", "Armorpiercing"]}
]

def write_constants_file():
    """
    Generate a Python file containing hardcoded constants for all packed columns
    so the IDE can autocomplete them.
    """

    output_path = "src/data/generated_constants.py"
    constant_dict = {}

    lines = []
    lines.append("# AUTO-GENERATED FILE — DO NOT EDIT BY HAND\n")
    lines.append("# Generated by gameDataClasses.write_constants_file()\n\n")

    #MANUAL
    constant_dict = {"X": 0, "Y": 1, "ALT": 2, "MAXDISTANCE": 5, "AP": 0, "DP": 0} #from manual

    lines.append(f"# Constants (manual) assorted \n")
    lines.append(f"MAXDISTANCE = 5\n") #max distance of ranged attack (walker). Could actually get this from GameData... ugh. Contants not needed for loader.
    lines.append("\n")

    lines.append(f"# Constants (manual) for unitHexes 2nd dim (hex coords) and new table from flattening UnitTerrainAltitudes\n")
    lines.append(f"X = 0\n")
    lines.append(f"Y = 1\n")
    lines.append(f"ALT = 2\n")
    lines.append("\n")

    lines.append(f"# Constants (manual) for new table from flattening COMBAT \n")
    lines.append(f"AP = 0\n")
    lines.append(f"DP = 1\n")
    lines.append("\n")

    #AUTOMATIC
    # Iterate through your raw structure
    for d in gamedata_raw_structure:
        
        # Optional: write a section header
        if "name" in d:
            lines.append(f"# Constants for {d['name']}\n")

        packed_cols = d["packed_cols"]
        for i, packed_col in enumerate(packed_cols):
            const_name = packed_col.strip().upper().replace(" ", "_")
            if const_name in constant_dict:
                if constant_dict[const_name] != i: raise RuntimeError(f"{const_name} is duplicate with conflicting values")
            lines.append(f"{const_name} = {i}\n")

        lines.append("\n") #space before next section

    # Write / overwrite the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # print(f"Generated constants file at: {os.path.abspath(output_path)}")
write_constants_file()

@dataclass(frozen=True)
class GameData:
    Abilities:              NDArray[np.bool_]                   =field(default_factory=np.ndarray, metadata={"dtype": np.bool_})
    Altitudes:              NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    Maptags:                NDArray[np.str_]                    =field(default_factory=np.ndarray, metadata={"dtype": np.str_})
    Races:                  NDArray[np.str_]                    =field(default_factory=np.ndarray, metadata={"dtype": np.str_})
    TerrainAltitudes:       NDArray[np.bool_]                   =field(default_factory=np.ndarray, metadata={"dtype": np.bool_})
    Terrains:               NDArray[np.str_]                    =field(default_factory=np.ndarray, metadata={"dtype": np.str_})
    UnitAbilities:          NDArray[np.uint8]                   =field(default_factory=np.ndarray, metadata={"dtype": np.uint8})
    UnitAltitudes:          NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    Units:                  NDArray[np.uint8]                   =field(default_factory=np.ndarray, metadata={"dtype": np.uint8})
    UnitTerrains:           NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    Unittypes:              NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    UnittypeTerrains:       NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    UnitUnittypeAltitudes:  NDArray[np.float16]                 =field(default_factory=np.ndarray, metadata={"dtype": np.float16})

    #Flattened stuff
    #UnitAbilities and UnitTerrains just modified
    UnitTerrainAltitudes:   Optional[np.int8]                   =field(default=None, metadata={"dtype": np.int8})
    Combat:                 Optional[np.float16]                =field(default=None, metadata={"dtype": np.float16}) 
#endregion

#region Hex and Action, subcomponents... mathy stuff, idk

@dataclass(frozen=True)
class clsHex:
    x:                      np.uint8 #not allowing negatives because this are indices of the map numpy array
    y:                      np.uint8 
    altitude:               np.uint8

@dataclass(frozen=True)
class clsAction:
    UnitIndex:              np.uint8
    AbilityNumber:          np.uint8
    BeforeAttackHex:        clsHex
    DefenderUnitIndex:      np.uint8
    AfterAttackHex:         clsHex

# class ActionLike(Protocol): #this was supposed to help with autocomplete but doesn't
#     UnitIndex:              np.uint8
#     AbilityNumber:          np.uint8
#     BeforeAttackHex:        clsHex
#     AfterAttackHex:         np.uint8
#     AfterAttackHex:         clsHex

#endregion