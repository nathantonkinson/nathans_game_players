#the engine has
    # an internal GameState
    # is created from a GameState
    # takes in actions to alter state
    # exposes functions like available moves


#higher level not-AI important stuff can be full classes, not here

from __future__ import annotations #supposed to help with autocomplete, must be before other imports

import numpy as np
import math
from math import comb
import random



import src.data.gameDataClasses as dc
from src.data.gameDataClasses import GameState, GameData, clsAction, clsHex
import src.data.generated_constants as gc


class Engine:
    def __init__(self, gamestate: GameState, gamedata: GameData):
        self.GameState: GameState = gamestate #is a GameState data class
            #might need to make this private somehow and expose function only? for FOW 
        #probably read rule configs from game state? maybe not
        self.GameData: GameData = gamedata

        self.availableActions = []

        # #shortcut stuff, need to update when actions taken
        # self.unitDefenses = np.ndarray
        # self.hexUnits = np.ndarray
        # self.unitMobility = np.ndarray
        # self.unitRangemin = np.ndarray
        # self.unitRangemax = np.ndarray
        
        #maybe an np array of shape (unit_index, 9 or so) for all the unit properties - not a ton faster than individual arrays
    
    def getAvailableActions(self):
        #returns list of actions (with their move before and after included) available to all units
        #probably iterates through all units
        availableActions = [] #items are (unit index, ability number, )
        for n, up in self.gamestate.Units.UnitPlayers:
            if up == self.gamestate.MetadataCurrent.CurrentTurn:
                availableActions.append(self.getAvailableActionsUnit(n))
        return availableActions
    
    def getAvailableActionsUnit(self, unit_index):
        #returns list of actions (with their move before and after included) available to unit of given index

        #lookup unit number
        #get a list of all its active abilities - probably build in the loader (or elsewhere) this pre-built as one table
        #for the ones that involve movement, do pathing, attack selection, pathing if relevant

        unitnum = self.GameState.Units.UnitNumbers(unit_index)
        # AvailableActions = 
            #load all default activeabilities
            #load the overrides

        return None
    
    def getAvailableMoves(self, unit_index, start_hex_tuple):
        #this can be called on the moveAfterAttack, so unit data will not be of its start movement position
        #start hex tuple is (x, y, state), get the unit type from unit_index
        #returns valid destination hex

        return None
    
    def applyAction(self, action: clsAction):
        #what is the form of the action?
            #unit index, active ability number perhaps, move to xy, attack unit index, final position xystate
        
        #validate action is in list of actions
        
        #do we put all the abilities in here, or in separate file?

        match action.AbilityNumber:
            case 1: #attack
                #? validate it can move there and there is a target (and target in range)
                    # current hex = self.GameState.Units.UnitHexes(action.UnitIndex)
                attackerDead = False

                #region DO DAMAGE CALC BIG STUFF
                #if attack is only one directional, don't need some of these

                #nonuniform non-else dependent info
                attackerUnitIndex = action.UnitIndex
                defenderUnitIndex = action.DefenderUnitIndex
                attackerX = action.BeforeAttackHex.x
                defenderX = self.GameState.Units.UnitHexes[(defenderUnitIndex, gc.X)]
                attackerY = action.BeforeAttackHex.y
                defenderY = self.GameState.Units.UnitHexes[(defenderUnitIndex, gc.Y)]
                attackerAltitude = action.BeforeAttackHex.altitude
                defenderAltitude = self.GameState.Units.UnitHexes[(defenderUnitIndex, gc.ALT)]
                
                #uniform, not dependent on other unit, gamestate
                attackerUnitHp = self.GameState.Units.UnitHps[attackerUnitIndex]
                defenderUnitHp = self.GameState.Units.UnitHps[defenderUnitIndex]
                attackerUnitNumber = self.GameState.Units.UnitNumbers[defenderUnitIndex]
                defenderUnitNumber = self.GameState.Units.UnitNumbers[defenderUnitIndex]
                attackerTerrainNumber = self.GameState.Map.Map[(attackerX, attackerY)]
                defenderTerrainNumber = self.GameState.Map.Map[(defenderX, defenderY)]
                #uniform, all gamedata lookups
                attackerUnittype = self.GameData.Units[(attackerUnitNumber, gc.UNITTYPENUMBER)]
                defenderUnittype = self.GameData.Units[(defenderUnitNumber, gc.UNITTYPENUMBER)]
                attackerTerrainAtk = self.GameData.UnittypeTerrains[(attackerUnittype, attackerTerrainNumber, gc.ATTACKBONUS)]
                defenderTerrainAtk = self.GameData.UnittypeTerrains[(defenderUnittype, defenderTerrainNumber, gc.ATTACKBONUS)]
                attackerTerrainDef = self.GameData.UnittypeTerrains[(attackerUnittype, attackerTerrainNumber, gc.DEFENSEBONUS)]
                defenderTerrainDef = self.GameData.UnittypeTerrains[(defenderUnittype, defenderTerrainNumber, gc.DEFENSEBONUS)]
                attackerAltitudeBonus = self.GameData.Altitudes[(attackerAltitude, gc.ATTACKBONUS)]
                defenderAltitudeBonus = self.GameData.Altitudes[(defenderAltitude, gc.ATTACKBONUS)]
                #if underground, will get 0s here... hm
                attackerRangeMin = self.GameData.UnitAltitudes[(attackerUnitNumber, attackerAltitude, gc.ATTACKRANGEMIN)]
                defenderRangeMin = self.GameData.UnitAltitudes[(defenderUnitNumber, defenderAltitude, gc.ATTACKRANGEMIN)]
                attackerRangeMax = self.GameData.UnitAltitudes[(attackerUnitNumber, attackerAltitude, gc.ATTACKRANGEMAX)]
                defenderRangeMax = self.GameData.UnitAltitudes[(defenderUnitNumber, defenderAltitude, gc.ATTACKRANGEMAX)]
                attackerDefense = self.GameData.UnitAltitudes[(attackerUnitNumber, attackerAltitude, gc.DEFENSE)]
                defenderDefense = self.GameData.UnitAltitudes[(defenderUnitNumber, defenderAltitude, gc.DEFENSE)]
                defenderDefenseTotal = defenderDefense + defenderTerrainDef
                attackerDefenseTotal = attackerDefense + attackerTerrainDef

                #depends on other unit
                attackerStrength = self.GameData.UnitUnittypeAltitudes[(attackerUnitNumber, defenderUnittype, defenderAltitude, gc.STRENGTH)]
                defenderStrength = self.GameData.UnitUnittypeAltitudes[(defenderUnitNumber, attackerUnittype, attackerAltitude, gc.STRENGTH)]
                attackerArmorpiercing = self.GameData.UnitUnittypeAltitudes[(attackerUnitNumber, defenderUnittype, defenderAltitude, gc.ARMORPIERCING)]
                defenderArmorpiercing = self.GameData.UnitUnittypeAltitudes[(defenderUnitNumber, attackerUnittype, attackerAltitude, gc.ARMORPIERCING)]
                
                #endregion a bunch of attack stats

                #attacker specific and other stuff not implemented yet
                gangupBonus = 0
                popupBonus = 0
                attackerVeterancy = 0
                defenderVeterancy = 0

                #retaliation check by dist
                #CHECK kraken/skimmer attack from underwater
                dist = self.getDist(attackerX, attackerY, defenderX, defenderY)
                #check if defender can retaliate
                retaliation = False if dist > defenderRangeMax or dist < defenderRangeMin else True

                #attacker damage inflicted
                if True:
                    attackerP = (
                        0.5
                        + 0.05*(attackerStrength + attackerTerrainAtk + attackerAltitudeBonus + attackerVeterancy)
                        + 0.05*(gangupBonus + popupBonus)
                        - 0.05*defenderDefenseTotal
                        + 0.05*(math.floor(attackerArmorpiercing*defenderDefenseTotal*5)/5) #round down to nearest 0.2 (before multiply by 0.05)
                        )
                    damage = self.calcDamage(attackerUnitHp, attackerP)
                    new_hp = max(0, defenderUnitHp - damage)
                    #do it
                    if new_hp == 0:
                        self.destroyUnit(defenderUnitIndex)
                        #let the system know there's a new space open for movement and no ZOC
                    else:
                        self.GameState.Units.UnitHps[action.DefenderUnitIndex] = new_hp

                #reciprocal damage
                if retaliation == True:
                    defenderP = (
                        0.5
                        + 0.05*(defenderStrength + defenderTerrainAtk + defenderAltitudeBonus + defenderVeterancy)
                        # + 0.05*() #no gang up or popup for retaliation
                        - 0.05*attackerDefenseTotal
                        + 0.05*(math.floor(defenderArmorpiercing*attackerDefenseTotal*5)/5) #round down to nearest 0.2 (before multiply by 0.05)
                        )
                    damage = self.calcDamage(defenderUnitHp, defenderP)
                    new_hp = max(0, attackerUnitHp - damage)
                    #do it
                    if new_hp == 0:
                        self.destroyUnit(attackerUnitIndex)
                        attackerDead = True
                        #if unit destroyed... no move after attack. We know that due to available actions... hm
                    else:
                        self.GameState.Units.UnitHps[action.UnitIndex] = new_hp

                #if it's still alive, do move after attack if that's a thing
                if attackerDead == False:  
                    pass

                #update it's position
                if attackerDead == False:
                    self.GameState.Units.UnitHexes[attackerUnitIndex] = [action.AfterAttackHex.x, action.AfterAttackHex.y, action.AfterAttackHex.altitude]

            case 24: #move 
                #validate it can move there
                pass
            case 6: #repair - or if repairing is disabled, this is a do-nothing. (or perhaps we can move into our own square?)
                pass
        
    def calcDamage(self, h, p):


        def dmg_byMath(h, p, x): #correct (at least quite close)
            n = 12 * h
            lo = 12 * x
            hi = 12 * x + 11
            return sum(comb(n, k) * p**k * (1-p)**(n-k) for k in range(lo, hi+1))
        
        def avg_byMath(h, p):
            #calculate average damage expected using the fancy math instead of simulations 
            dmg = 0
            if h>12: raise RuntimeError("H can't be larger than 12")
            for x in range(0, 13, 1): #1 to 12
                dmg += x*dmg_byMath(h, p, x)
            return round(x, 0)
        
        def dmg_byOnce(h, p):
            #the actual way the game does it
            hits = 0
            for _ in range(h*12):
                if random.random() <= p:
                    hits += 1
            return math.floor(hits/12)

        # return dmg_byMath(h, p)
        return dmg_byOnce(h, p)
    
    def getDist(self, x1, y1, x2, y2):
        #distance between
        #coords should never be negative but this function works either way
        #adjacents: (-1, 1), (0, 1), (-1, 0), (1, 0), (0, -1), (1, -1)
        xdiff = x1-x2
        ydiff = y1-y2
        xsign = np.sign(xdiff)
        ysign = np.sign(ydiff)
        if xsign == 0 or ysign == 0 or xsign == ysign:
            return abs(xdiff) + abs(ydiff)
        else: #one sign negative, the other positive, using the +1+1 diagonals
            return max(abs(xdiff), abs(ydiff))
    
    def destroyUnit(self, unit_index):
        #delete unit
        #newly created units can take the slot later
        #let the system know there's a new space open for movement and no ZOC
        
        #zero out the info
        self.GameState.Units.UnitHps[unit_index] = 0
        self.GameState.Units.UnitNumbers[unit_index] = 0
        self.GameState.Units.UnitPlayers[unit_index] = 0 #players indexed at 1
        self.GameState.Units.UnitHexes[unit_index, :] = 0 #x, y, and altitude
        #other properties like plauge, cooldown, etc
        
        #update available actions - let the system know there's a new space open for movement and no ZOC
        #all actions that are turned off due to friendly occupation of the prior space
        #turn off all actions that used the destination space
        #recalc all units that have actions that are adjacent to dead enemy

    def buildHelperArrays(self):
        #creates/full refreshes unitDefenses which is unit normal defense + terrain bonus + submerged bonus 
        self.unitDefenses = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.int8)
        
        # self.unitDefenses = np.ndarray
        # self.hexUnits = np.ndarray
        # self.unitMobility = np.ndarray
        # self.unitRangemin = np.ndarray
        # self.unitRangemax = np.ndarray

        pass
    
    def passTurn(self):
        #alter metadata passing turn
        #generate more rng
        #could put this in the ability file
        pass

# initialState = GameState(metadataInitial=None, map=None, metadataCurrent=None, units=GameUnits(unitNumbers=np.zeroes(10, dtype=np.int8), unitHps=None, unitTiles=None, tileUnits=None))
# print(initialState.units.unitHps)
# myEngine = Engine("stuff")

