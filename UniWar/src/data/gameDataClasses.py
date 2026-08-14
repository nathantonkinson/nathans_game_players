#dataclasses, as well as data structure of my input csv data (loader is generic)

from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray
from typing import Optional, List, Protocol, TYPE_CHECKING
from enum import IntEnum
import sys
import os
import copy

import src.data.generated_constants as gc
if TYPE_CHECKING:
    from src.engine.engine import clsEngine #this would normally get circular problems without type_checking (or we could separate the dataclasses into separate files)


#region old game data (list of dataclasses)
# #region dataclass for each table
# @dataclass(frozen=True)
# class DataAbilities:
#     Name:               str
#     Number:             int
#     RequiresAction:     bool
#     AllowMovement:      bool #maybe can be nullable for the ones that don't require action?
#     Notes:              str

# @dataclass(frozen=True)
# class DataAltitudes:
#     Name:               str
#     Number:             int
#     AttackModifier:     int #for -2 underwater and -100 underground (not valid to attack anything from underground, even enemy underground units)

# @dataclass(frozen=True)
# class DataMaptags: #all hardcoded... do we even want this table? Maybe for visualization...
#     Name:               str
#     Number:             int
#     Notes:              str

# @dataclass(frozen=True)
# class DataRaces:
#     Name:               str
#     Number:             int

# @dataclass(frozen=True)
# class DataTerrainAltitudes:
#     TerrainName:        str #can be deduced from #
#     TerrainNumber:      int
#     AltitudeName:       str #can be deduced from #
#     AltitudeNumber:     int
#     Allowed:            bool

# @dataclass(frozen=True)
# class DataTerrains:
#     Name:               str
#     Number:             int
#     Notes:              str

# @dataclass(frozen=True)
# class DataUnitAbilities:
#     UnitName:           str #deduced from #
#     UnitNumber:         int
#     AbilityName:        str #deduced
#     AbilityNumber:      int
#     Notes:              str
#     Cooldown:           int
#     AbilityStrength:    int

# @dataclass(frozen=True)
# class DataUnitAltitudes:
#     UnitRaceName:       str #deduced
#     UnitName:           str #deduced
#     UnitNumber:         int
#     AltitudeName:       str #deduced
#     AlttitudeNumber:    int
#     Mobility:           int
#     Vision:             int
#     AttackRangeMin:     int
#     AttackRangeMax:     int
#     Defense:            int

# @dataclass(frozen=True)
# class DataUnits:
#     RaceName:           str #deduced
#     RaceNumber:         int
#     Name:               str
#     Number:             int
#     Cost:               int #nullable for the converted ones
#     UnittypeName:       str #deduced
#     UnittypeNumber:     int
#     Repair:             int
#     ActionsPerTurn:     int
#     Notes:              str

# @dataclass(frozen=True)
# class DataUnitTerrains:
#     UnitName:           str #deduced
#     UnitNumber:         int
#     TerrainName:        str #deduced
#     TerrainNumber:      int
#     MobilityCost:       int
#     AttackBonus:        int
#     DefenseBonus:       int
#     MovementAllowed:    bool
#     Notes:              str

# @dataclass(frozen=True)
# class DataUnittypes:
#     Name:               str
#     Number:             int
#     Notes:              str

# @dataclass(frozen=True)
# class DataUnittypeTerrains:
#     UnittypeName:       str #deduced
#     UnittypeNumber:     int
#     TerrainName:        str #deduced
#     TerrainNumber:      int
#     MobilityCost:       int
#     AttackBonus:        int
#     DefenseBonus:       int
#     MovementAllowed:    bool #default yes, if no row then no
#     Notes:              str

# @dataclass(frozen=True)
# class DataUnitUnittypeAltitudes:
#     UnitRaceName:           str #deduced
#     UnitName:               str
#     UnitNumber:             int
#     DefenderUnittypeName:   str #deduced
#     DefenderUnittypeNumber: int
#     DefenderAltitudeName:   str #deduced
#     DefenderAltitudeNumber: int
#     Strength:               int
#     Armorpiercing:          int 

# #endregion game data individual tables

# # @dataclass(frozen=True)
# # class clsGameData:
# #     Abilities:              List[DataAbilities]                 =field(default_factory=list)
# #     Altitudes:              List[DataAltitudes]                 =field(default_factory=list)
# #     Maptags:                List[DataMaptags]                   =field(default_factory=list)
# #     Races:                  List[DataRaces]                     =field(default_factory=list)
# #     TerrainAltitudes:       List[DataTerrainAltitudes]          =field(default_factory=list)
# #     Terrains:               List[DataTerrains]                  =field(default_factory=list)
# #     UnitAbilities:          List[DataUnitAbilities]             =field(default_factory=list)
# #     UnitAltitudes:          List[DataUnitAltitudes]             =field(default_factory=list)
# #     Units:                  List[DataUnits]                     =field(default_factory=list)
# #     UnitTerrains:           List[DataUnitTerrains]              =field(default_factory=list)
# #     Unittypes:              List[DataUnittypes]                 =field(default_factory=list)
# #     UnittypeTerrains:       List[DataUnittypeTerrains]          =field(default_factory=list)
# #     UnitUnittypeAltitudes:  List[DataUnitUnittypeAltitudes]     =field(default_factory=list)

#endregion old game data class (list of dataclasses)

#region gamedata (np game data indexed)

#see flattening stuff in that file

gamedata_raw_structure = [
    {"csv": "Abilities", "dtype": np.bool_, "solo_cols":["Number"], "packed_cols": ["RecordExists", "RequiresAction", "Default", "AllowMovement"]}
    , {"csv": "Abilities", "field": "Abilities_Name", "dtype": object, "solo_cols":["Number"], "packed_cols": ["Name", "Notes"]}
    , {"csv": "Altitudes", "dtype": np.int8, "solo_cols":["Number"], "packed_cols": ["AttackBonus"]}
    , {"csv": "Altitudes", "field": "Altitudes_Name", "dtype": object, "solo_cols":["Number"], "packed_cols": ["Name", "Notes"]}
    , {"csv": "Maptags", "field": "Maptags_Name", "dtype": object, "solo_cols":["Number"], "packed_cols":["Name", "Notes"]}
    , {"csv": "Races", "field": "Races_Name", "dtype": object, "solo_cols":["Number"], "packed_cols":["Name", "Notes"]}
    , {"csv": "TerrainAltitudes", "dtype": np.bool_, "solo_cols":["TerrainNumber", "AltitudeNumber"], "packed_cols": ["Allowed"]}
    , {"csv": "Terrains", "field": "Terrains_Name", "dtype": object, "solo_cols":["Number"], "packed_cols":["Name", "Notes"]}
    , {"csv": "UnitAbilities", "dtype": np.uint8, "solo_cols":["UnitNumber", "AbilityNumber"], "packed_cols": ["RecordExists", "Cooldown", "AbilityStrength"]}
    , {"csv": "UnitAltitudes", "dtype": np.int8, "solo_cols":["UnitNumber", "AltitudeNumber"], "packed_cols": ["RecordExists", "Mobility", "Vision", "AttackRangeMin", "AttackRangeMax", "Defense"]}
    , {"csv": "Units", "dtype": np.uint8, "solo_cols":["Number"], "packed_cols": ["RaceNumber", "Cost", "UnittypeNumber", "UnitroleNumber", "RepairRate", "ActionsPerTurn"]}
    , {"csv": "Units", "field": "Units_Name", "dtype": object, "solo_cols":["Number"], "packed_cols":["Name", "Notes", "Abbreviation"]} #include RaceName or do that with flattening or..?
    , {"csv": "UnitTerrains", "dtype": np.int8, "solo_cols":["UnitNumber", "TerrainNumber"], "packed_cols":[ "AttackBonus", "DefenseBonus", "MovementAllowed", "MobilityCost"]}
    , {"csv": "Unittypes", "field": "Unittypes_Name", "dtype": object, "solo_cols":["Number"], "packed_cols":["Name", "Notes"]}
    , {"csv": "UnittypeTerrains", "dtype": np.int8, "solo_cols":["UnittypeNumber", "TerrainNumber"], "packed_cols":["AttackBonus", "DefenseBonus", "MovementAllowed", "MobilityCost"]}
    , {"csv": "UnitUnittypeAltitudes", "dtype": np.float16, "solo_cols":["UnitNumber", "DefenderUnittypeNumber", "DefenderAltitudeNumber"], "packed_cols":["Strength", "Armorpiercing"]}
]

@dataclass(frozen=True)
class clsGameData:
    Abilities:              NDArray[np.bool_]                   =field(default_factory=np.ndarray, metadata={"dtype": np.bool_})
    Abilities_Name:         NDArray                             =field(default_factory=np.ndarray, metadata={"dtype": object})
    Units:                  NDArray[np.uint8]                   =field(default_factory=np.ndarray, metadata={"dtype": np.uint8})
        #out of order for generated constants agreement with clsGameState
    Altitudes:              NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    Altitudes_Name:         NDArray                             =field(default_factory=np.ndarray, metadata={"dtype": object})
    Maptags_Name:           NDArray                             =field(default_factory=np.ndarray, metadata={"dtype": object})
    Races_Name:             NDArray                             =field(default_factory=np.ndarray, metadata={"dtype": object})
    TerrainAltitudes:       NDArray[np.bool_]                   =field(default_factory=np.ndarray, metadata={"dtype": np.bool_})
    Terrains_Name:          NDArray                             =field(default_factory=np.ndarray, metadata={"dtype": object})
    UnitAbilities:          NDArray[np.uint8]                   =field(default_factory=np.ndarray, metadata={"dtype": np.uint8})
    UnitAltitudes:          NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    Units_Name:             NDArray                             =field(default_factory=np.ndarray, metadata={"dtype": object})
    UnitTerrains:           NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    Unittypes_Name:         NDArray                             =field(default_factory=np.ndarray, metadata={"dtype": object})
    UnittypeTerrains:       NDArray[np.int8]                    =field(default_factory=np.ndarray, metadata={"dtype": np.int8})
    UnitUnittypeAltitudes:  NDArray[np.float16]                 =field(default_factory=np.ndarray, metadata={"dtype": np.float16})

    #Flattened stuff
    #UnitAbilities and UnitTerrains just modified
    UnitTerrainAltitudes:   Optional[np.int8]                   =field(default=None, metadata={"dtype": np.int8})
    # Combat:                 Optional[np.float16]                =field(default=None, metadata={"dtype": np.float16}) 

#endregion

#region Loc, Action, GUB, player, other subcomponents... mathy stuff, idk. Needed to construct gamestate

@dataclass(frozen=True)
class clsLoc:
    X:                      np.uint8 #not allowing negatives because this are indices of the map numpy array
    Y:                      np.uint8 
    Altitude:               np.uint8

@dataclass #(frozen=True) we build these sequntially, too much work
class clsAction:
    UnitIndex:              np.uint8
    AbilityNumber:          np.uint8
    DefenderUnitIndex:      np.uint8        = field(default=255)
    Enabled:                np.bool_        = field(default=True)
    BeforeAttackLoc:        clsLoc          = field(default=None)
    AfterAttackLoc:         clsLoc          = field(default=None)
    
    

@dataclass
class clsGUB:
    DefenderIndex:          np.uint8            = field(default=None)
    AttackerLoc:            tuple               = field(default=(0, 0, gc.DEFAULTALTITUDE))

#clsPlayer used in frozen gamestate metadata
@dataclass
class clsPlayer:
    Race:                   np.int8             = field(default=None)
    InitialCredits:         np.int8             = field(default=0)
    Team:                   np.int8             = field(default=None)
    AllowedRaces:           set[int]            = field(default_factory=set) #allows any race.

#endregion

#region gameState

#frozen stuff
@dataclass #we turned off frozen, not sure it helps much, and causing problems with references and stuff I want to do
#we don't need to make the metadata portion super small and fast, since it won't be copied. But doing so anyway for the moment
class clsMetadataInitial:
    MapName:        np.str_
    PlayersInitial: list[clsPlayer]             = field(default_factory=list) #for some reason it doesn't like NDArray[object] should be filled with identical dicts with race, team, maybe credits
    MapDescription: np.str_                     = field(default=None)
    AllowedRaces:   set[int]                    = field(default_factory=set) #allows any race. At idx3 because of gc
    Username:       np.str_                     = field(default=None)
    StartingCredits: np.uint16                  = field(default=0)
    BaseCredits:    np.uint16                   = field(default=100)
    CityCredits:    np.uint16                   = field(default=None) #I think the actual game you cannot customize this?
    Hashtags:       Optional[NDArray[np.str_]]  = field(default_factory=np.ndarray)
    WinCon:         np.int8                     = field(default=3) #capture/cover enemy bases and kill all their units.

    def __post_init__(self):
        # assert self.playersInitial.ndim == 1 #how do we check this is filled with dicts or whatever it is?
        pass
    
#non frozen stuff
@dataclass
class clsMetadataCurrent:
    PlayersCredits:     NDArray[np.uint16]          = field(metadata={"dtype": np.uint16})
    PlayersKills:       NDArray[np.uint32]          = field(default=None, metadata={"dtype": np.uint32}) 
    WinnerTeam:         np.uint8                    = field(default=None, metadata={"dtype": np.uint8})
    RandomState:        dict                        = field(default_factory=dict) #np.random.default_rng().bit_generator.state
        #this is actually only used in load/reload, normally just the engine.rng is copied
    GangUpBonus:        clsGUB                      = field(default=None) #defender index, attacked from loc 
    #\/ these three keep time
    CurrentRound:       np.uint8                    = field(default=1)
    CurrentPlayer:      np.uint8                    = field(default=0, metadata={"dtype": np.uint8}) #starts at 0
    CurrentAction:      np.uint16                   = field(default=0) #action index within the current turn
    

    def __post_init__(self):
        assert self.PlayersCredits.ndim == 1, "Players credits should be 1 dim array"

@dataclass
class clsGameUnits:
    #all of these are 1d np arrays of length of the number of units possible. We will reshape on engine load
    UnitPlayers:    NDArray[np.int8]                = field(metadata={"dtype": np.uint8})
    UnitNumbers:    NDArray[np.uint8]               = field(metadata={"dtype": np.uint8}) #capping out at 256 unit types lol
    UnitHps:        NDArray[np.uint8]               = field(metadata={"dtype": np.uint8})
    UnitHexes:      NDArray[np.uint8]               = field(metadata={"dtype": np.uint8}) #shape (U index, 3 (H, W, S))
    UnitActions:    Optional[NDArray[np.uint8]]     = field(metadata={"dtype": np.uint8})
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
class clsGameState:
    # def __init__(self): #I think this will be more costly, and/or isn't actually using the dataclass features
    MetadataInitial:    clsMetadataInitial          = field()        
    Map:                NDArray[np.uint8]           = field(metadata={"dtype": np.uint8}) #dimensions set when initialized
        #potenitally could put the unittype movement cost in each tile for faster lookup? since this is immutable
            #would this be faster?
        #units are adjacent to: (-1, 1), (0, 1), (-1, 0), (1, 0), (0, -1), (1, -1)
            #y axis is slanted right into +x+y on normal graph
    Units:              clsGameUnits                = field(default=None)
    MetadataCurrent:    clsMetadataCurrent          = field(default=None)
    BasePlayers:        NDArray[np.int8]            = field(default=None, metadata={"dtype": np.int8}) #2 dim: (x, y, player index)*qty bases

    def __post_init__(self):
            assert self.Map.ndim == 2, "Map should be 2 dimensional (x, y)" #state is for units, terrain types have states built in

#endregion gamestate

#region advanced stuff outside of engine, relies on GameState
@dataclass
class clsReplayCheckpoint:
    GameState:          clsGameState                = field()

@dataclass
class clsReplay:
    Actions:            list[clsAction]             = field()
    Map:                clsGameState                = field()
    MapFilename:        str                         = field(default=None)
    Checkpoints:        list[object]                = field(default=None)

@dataclass
class clsNode:
    ParentNode:         "clsNode | None"            = field(default=None) #quotes mean resolve later
    Action:             clsAction                   = field(default=None)
    Depth:              np.uint8                    = field(default=None)
    NodeEngine:         "clsEngine | None"          = field(default=None)
    Heuristic:          np.float_                   = field(default=None)
    Stability:          np.float_                   = field(default=None)

#endregion advanced stuff outside of engine



