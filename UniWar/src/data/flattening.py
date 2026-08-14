#flattens GameData for less lookups in the engine
#do we even want this, or just have our raw csv game data be flat anyway? eh I like relational structures
#does not cover the utility stuff (like HexUnits) in the engine itself

#let's not do the middle-flat strategy, just full flat


# from copy import deepcopy
import dataclasses as dc
from dataclasses import replace
import numpy as np
import math

import src.data.generated_constants as gc
from src.data.gameDataClasses import clsGameData, clsGameState, clsAction, clsLoc


#region FLATTEN STRAT (kindof old)

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


def flattenUnitAbilities(GameData: clsGameData):
    # GameData.UnitAbilities #specifics
    # GameData.Abilities #defaults
    out = np.zeros((
        len(GameData.Units)
        , len(GameData.Abilities)
        , GameData.UnitAbilities.shape[2]
        ), dtype=np.uint8)

    for u, unit in enumerate(GameData.Units):
        if unit[gc.UNITTYPENUMBER] == 0: continue #no data on this unit, unused
        #add in all default actions
        for a, ability in enumerate(GameData.Abilities):
            #if our logic required falses, how would we skip over unused ability numbers?
            if ability[gc.RECORDEXISTS] == True and ability[gc.DEFAULT] == True: #not using and ability[gc.REQUIRESACTION] == True
                out[(u, a, gc.RECORDEXISTS)] = 1
        #overrides
        if u < len(GameData.UnitAbilities): #not all units represented in UnitAbilities, so don't max it out
            for a, ability in enumerate(GameData.UnitAbilities[u]):
                #can't tell if it doesn't exist in the list... hm.
                if ability[gc.RECORDEXISTS] == 1:
                    if out[(u, a, 1)] == 1: 
                        out[(u, a)] = 0
                    else:
                        out[(u, a)] = ability
    

    #can do replace but can't modify in-place so pass out
    return dc.replace(GameData, UnitAbilities = out)

def flattenUnitTerrains(GameData: clsGameData):
    #flatten unittypeTerrains into unitTerrains, all because of the silly Battery exception lol

    out = np.zeros((
        len(GameData.Units)
        , len(GameData.Terrains_Name)
        , GameData.UnittypeTerrains.shape[2]
        ), dtype=np.int8)
    #rule = unittypeTerrains
    #exception = UnitTerrains

    #rule = unittypeTerrains
    for u, unit in enumerate(GameData.Units):
        for t in range(GameData.UnittypeTerrains.shape[1]):
            if unit[gc.UNITTYPENUMBER] >= GameData.UnittypeTerrains.shape[0]: #>= because indexed at 0 etc
                pass #it's already loaded with zeroes
            else:
                out[(u, t)] = GameData.UnittypeTerrains[(unit[gc.UNITTYPENUMBER], t)]

    #exception = UnitTerrains
    for u in range(GameData.UnitTerrains.shape[0]):
        for t in range(GameData.UnitTerrains.shape[1]):
            if GameData.UnitTerrains[(u, t, gc.MOBILITYCOST)] > 0: #we don't have an "exists" col here, but this should work
                out[(u, t)] = GameData.UnitTerrains[(u, t)]

    return dc.replace(GameData, UnitTerrains = out)

def flattenUnitTerrainAltitudes(GameData: clsGameData):
    #similar code to UnitTerrains and not dependent on that one running

    out = np.zeros((
        len(GameData.Units)
        , len(GameData.Terrains_Name)
        , len(GameData.Altitudes)
        , GameData.UnittypeTerrains.shape[2] #atk, def, allowed, cost
        ), dtype=np.int8) 
    
    #1st generic rule, terrain altitude movement allowed
    for t in range(GameData.TerrainAltitudes.shape[0]): #cells outside filled range are 0s
        for a in range(GameData.TerrainAltitudes.shape[1]):
            out[:, t, a, gc.MOVEMENTALLOWED] = int(GameData.TerrainAltitudes[(t, a)])

    #cost rule = unittypeTerrains, for where movement is allowed
    for u, unit in enumerate(GameData.Units):
        for t in range(GameData.UnittypeTerrains.shape[1]):
            for a in range(len(GameData.Altitudes)):
                if out[(u, t, a, gc.MOVEMENTALLOWED)] == 1: 
                    if unit[gc.UNITTYPENUMBER] < GameData.UnittypeTerrains.shape[0]:
                        out[u, t, a] = GameData.UnittypeTerrains[(unit[gc.UNITTYPENUMBER], t)]

    #exception = UnitTerrains. Does not cause movement allowed, but may turn it off I guess
    for u in range(GameData.UnitTerrains.shape[0]):
        for t in range(GameData.UnitTerrains.shape[1]):
            if GameData.UnitTerrains[(u, t, gc.MOBILITYCOST)] > 0: #we don't have an "exists" col here, but this should work
                if out[(u, t, a, gc.MOVEMENTALLOWED)] == 1: 
                    out[u, t, a] = GameData.UnitTerrains[(u, t)]

    return dc.replace(GameData, UnitTerrainAltitudes = out)

def flattenCombat(GameData: clsGameData):
    #ABANDONED because 32m is slower than 22 individual lookups

    #make np array such that you input attacker and defender stats and get two ps
        #DOES NOT INCLUDE veterancy, gang-up, popup
        #return p=-1 for when damage impossible (out of range or not allowed or whatever) (so the other bonuses don't outweigh)
    #STATS
        #2x unitnumber
        #2x terraintype
        #2x altitude
        #1x distance
    
    #COMBAT TABLE - BOTH p values right?
        #attacker unit number
        #***defending unitnumber
        #***defending altitude
        #attacking unit terrain
        #***defending unit terrain
        #?? distance?
    #currently 34 entries
        #2x unit number
        #2x unit hp
        #6x position
        #2x terrain type
    #with savings would be
        #2x unit number
        #2x unit hp
        #6x position
        #2x terrain type
        #? distance
        #plug all this into big lookup to get the two ps
        #gets rid of 18 or so


    out = np.zeros((
        len(GameData.Units)
        , len(GameData.Units)
        , len(GameData.Terrains_Name)
        , len(GameData.Terrains_Name)
        , len(GameData.Altitudes)
        , len(GameData.Altitudes)
        , gc.MAXDISTANCE+1 #+1 bc includes 0
        , 2 #both ps (attacker then defender)
        ), dtype=np.float16)
    
    i = 0
    size = out.size
    print("Combat table generation")

    #this is 32m combinations... hm...
    for au, aunit in enumerate(GameData.Units):
        for du, dunit in enumerate(GameData.Units):
            for at in range(GameData.Terrains_Name.shape[0]):
                for dt in range(GameData.Terrains_Name.shape[0]):
                    for aa, aalt in enumerate(GameData.Altitudes):
                        for da, dalt in enumerate(GameData.Altitudes):
                            for d in range(out.shape[6]):
                                #progress bar
                                i += 1
                                if i % 10000 == 0:
                                    print(f"\r\033[KCombat table generation progress: {100*i/size:.1f}%", end="", flush=True)
                                #skips
                                if aa >= GameData.UnitUnittypeAltitudes.shape[2] or da >= GameData.UnitUnittypeAltitudes.shape[2]: continue #could put other skips here. This one needed because underground does not show up on some tables, so they have less dims.
                                if at >= GameData.UnittypeTerrains.shape[1] or dt >= GameData.UnittypeTerrains.shape[1]: continue

                                #do the whole calc

                                #uniform, all gamedata lookups
                                attackerUnittype = aunit[gc.UNITTYPENUMBER]
                                defenderUnittype = dunit[gc.UNITTYPENUMBER]
                                attackerTerrainAtk = GameData.UnittypeTerrains[(attackerUnittype, at, gc.ATTACKBONUS)]
                                defenderTerrainAtk = GameData.UnittypeTerrains[(defenderUnittype, dt, gc.ATTACKBONUS)]
                                attackerTerrainDef = GameData.UnittypeTerrains[(attackerUnittype, at, gc.DEFENSEBONUS)]
                                defenderTerrainDef = GameData.UnittypeTerrains[(defenderUnittype, dt, gc.DEFENSEBONUS)]
                                attackerAltitudeBonus = aalt[gc.ATTACKBONUS]
                                defenderAltitudeBonus = dalt[gc.ATTACKBONUS]
                                #if underground, will get 0s here... hm
                                attackerRangeMin = GameData.UnitAltitudes[(au, aa, gc.ATTACKRANGEMIN)]
                                defenderRangeMin = GameData.UnitAltitudes[(du, da, gc.ATTACKRANGEMIN)]
                                attackerRangeMax = GameData.UnitAltitudes[(au, aa, gc.ATTACKRANGEMAX)]
                                defenderRangeMax = GameData.UnitAltitudes[(du, da, gc.ATTACKRANGEMAX)]
                                attackerDefense = GameData.UnitAltitudes[(au, aa, gc.DEFENSE)]
                                defenderDefense = GameData.UnitAltitudes[(du, da, gc.DEFENSE)]
                                defenderDefenseTotal = defenderDefense + defenderTerrainDef
                                attackerDefenseTotal = attackerDefense + attackerTerrainDef

                                #depends on other unit
                                attackerStrength = GameData.UnitUnittypeAltitudes[(au, defenderUnittype, da, gc.STRENGTH)]
                                defenderStrength = GameData.UnitUnittypeAltitudes[(du, attackerUnittype, aa, gc.STRENGTH)]
                                attackerArmorpiercing = GameData.UnitUnittypeAltitudes[(au, defenderUnittype, da, gc.ARMORPIERCING)]
                                defenderArmorpiercing = GameData.UnitUnittypeAltitudes[(du, attackerUnittype, aa, gc.ARMORPIERCING)]

                                #p
                                if (
                                    attackerRangeMin <= d <= attackerRangeMax 
                                    and GameData.UnitAbilities[(au, 1, gc.RECORDEXISTS)] == 1 #index 1 = "attack" ability
                                    and attackerStrength > 0): 
                                    attackerP = (
                                        0.5
                                        + 0.05*(attackerStrength + attackerTerrainAtk + attackerAltitudeBonus)
                                        - 0.05*defenderDefenseTotal
                                        + 0.05*(math.floor(attackerArmorpiercing*defenderDefenseTotal*5)/5) #round down to nearest 0.2 (before multiply by 0.05)
                                    )
                                else:
                                    attackerP = -1
                                if (
                                    defenderRangeMin <= d <= defenderRangeMax 
                                    and GameData.UnitAbilities[(du, 1, gc.RECORDEXISTS)] == 1 #index 1 = "attack" ability:
                                    and defenderStrength > 0): 
                                    defenderP = (
                                        0.5
                                        + 0.05*(defenderStrength + defenderTerrainAtk + defenderAltitudeBonus)
                                        # + 0.05*() #no gang up or popup for retaliation
                                        - 0.05*attackerDefenseTotal
                                        + 0.05*(math.floor(defenderArmorpiercing*attackerDefenseTotal*5)/5) #round down to nearest 0.2 (before multiply by 0.05)
                                    )
                                else:
                                    defenderP = -1

                                out[(au, du, at, dt, aa, da, d, 0)] = attackerP
                                out[(au, du, at, dt, aa, da, d, 1)] = defenderP

    print() #exit newline shennanigans of progress bar
    return dc.replace(GameData, Combat = out)

def allFlattening(GameData: clsGameData):
    #does all the flattening in one bundle

    GameData = flattenUnitAbilities(GameData)
    GameData = flattenUnitTerrains(GameData) #are we going to even use this since we have the one crossed with altitudes (that doesn't depend on this)?
    GameData = flattenUnitTerrainAltitudes(GameData)
    # GameData = flattenCombat(GameData) #takes 2 minutes and is not faster than 22 lookups

    return GameData

