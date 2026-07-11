
from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray
from typing import Optional, List


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
    Hashtags:       Optional[NDArray[np.str_]]  = field(default=None)

    def __post_init__(self):
        # assert self.playersInitial.ndim == 1, how do we check this is filled with dicts or whatever it is?
        pass

#Could do map without dataclass but it might help if it's frozen (does it?)
@dataclass(frozen=True)
class GameMap:
    Map:                NDArray[np.uint8]           = field(metadata={"dtype": np.uint8}) #dimensions set when initialized
    #potenitally could put the unittype movement cost in each tile for faster lookup? since this is immutable
        #would this be faster?
    
    def __post_init__(self):
        assert self.Map.ndim == 2, "Map should be 3 dimensional (x, y)" #state is for units, terrain types have states built in

#endregion

#region gameState non-frozen
@dataclass
class GameMetadataCurrent:
    CurrentPlayer:        np.uint8                    = field(metadata={"dtype": np.uint8}) #starts at 0
    PlayersCredits:     NDArray[np.uint16]          = field(metadata={"dtype": np.uint16})

    def __post_init__(self):
        assert self.PlayersCredits.ndim == 1, "Players credits should be 1 dim array"

@dataclass
class GameUnits:
    UnitPlayers:    NDArray[np.uint8]               = field(metadata={"dtype": np.uint8})
    UnitNumbers:    NDArray[np.uint8]               = field(metadata={"dtype": np.uint8}) #capping out at 256 unit types lol
    UnitHps:        NDArray[np.uint8]               = field(metadata={"dtype": np.uint8})
    UnitHexes:      Optional[NDArray[np.uint8]]     = field(default=None, metadata={"dtype": np.uint8}) #shape (U index, 3 (H, W, S))
    HexUnits:       Optional[NDArray[np.uint8]]     = field(default=None, metadata={"dtype": np.uint8}) #shape (H, W, S) with no entries for places without units 
    # UnitNumbers:    np.ndarray                      = field(metadata={"dtype": np.uint8}) #capping out at 256 unit types lol
    # UnitHps:        np.ndarray                      = field(metadata={"dtype": np.uint8})
    # UnitHexes:      Optional[np.ndarray]            = field(default=None, metadata={"dtype": np.uint8}) #shape (U index, 3 (H, W, S))
    # HexUnits:       Optional[np.ndarray]            = field(default=None, metadata={"dtype": np.uint8}) #shape (H, W, S) with no entries for places without units 
    #some kind of special properties, like cooldowns, plague, emp

    def __post_init__(self):
        assert self.UnitPlayers.ndim == 1, "unit numbers must be 1D"
        assert self.UnitNumbers.ndim == 1, "unit numbers must be 1D"
        assert self.UnitHps.ndim == 1, "hp must be 1D"
        if self.UnitHexes is not None:
            assert self.UnitHexes.ndim == 2, "unit tiles must be 2D (unit_index, 2 (x and y))"
            assert self.UnitHexes.shape[1] == 3, "unit tiles 2nd dimension must be size 3 (for height, width, and state (surface air, underwater, underground))"
        if self.HexUnits is not None:
            assert self.HexUnits.ndim == 3, "tileUnits must be 3D, (x, y, state) = unit index"
            assert self.HexUnits.shape[2] == 3, "tileUnits 3rd dim must be size 3 state (surface air, underwater, underground)"
        pass

@dataclass
class GameState:
    # def __init__(self): #I think this will be more costly, and/or isn't actually using the dataclass features
    MetadataInitial:    GameMetadataInitial         = field()
    Map:                GameMap
        
    MetadataCurrent:    GameMetadataCurrent
    Units:              GameUnits                   = field()
        #duplicate data under here unitTiles and tilesUnit (or something)
    
#endregion non-frozen

#region game data (rules)

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

@dataclass(frozen=True)
class GameData:
    Abilities:              List[DataAbilities]                 =field(default_factory=list)
    Altitudes:              List[DataAltitudes]                 =field(default_factory=list)
    Maptags:                List[DataMaptags]                   =field(default_factory=list)
    Races:                  List[DataRaces]                     =field(default_factory=list)
    TerrainAltitudes:       List[DataTerrainAltitudes]          =field(default_factory=list)
    Terrains:               List[DataTerrains]                  =field(default_factory=list)
    UnitAbilities:          List[DataUnitAbilities]             =field(default_factory=list)
    UnitAltitudes:          List[DataUnitAltitudes]             =field(default_factory=list)
    Units:                  List[DataUnits]                     =field(default_factory=list)
    UnitTerrains:           List[DataUnitTerrains]              =field(default_factory=list)
    Unittypes:              List[DataUnittypes]                 =field(default_factory=list)
    UnittypeTerrains:       List[DataUnittypeTerrains]          =field(default_factory=list)
    UnitUnittypeAltitudes:  List[DataUnitUnittypeAltitudes]     =field(default_factory=list)