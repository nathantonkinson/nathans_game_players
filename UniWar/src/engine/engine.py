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
from dataclasses import replace
import copy
import heapq #used for movement

import src.data.gameDataClasses as dc
from src.data.gameDataClasses import GameState, GameData, clsAction, clsLoc
import src.data.generated_constants as gc


class Engine:
    def __init__(self, gamestate: GameState, gamedata: GameData):

        #GameState and GameData
        self.GameState: GameState = gamestate #is a GameState data class
            #might need to make this private somehow and expose function only? for FOW 
        #probably read rule configs from game state? maybe not
        self.GameData: GameData = gamedata

        #The gamestate should come in with race assignment already done... yeah?

        #Team assignment 
        nonblankTeam = False
        for p, player in enumerate(self.GameState.MetadataInitial.PlayersInitial):
            if player.Race is None: raise RuntimeError("Race unassigned at engine start")
            if player.Team is None:
                if nonblankTeam == True: raise RuntimeError("Teams partially assigned at engine start") 
                player.Team = p #teams are indexed at 0
            else:
                nonblankTeam = True

        #rng stuff
        #Call using rng.random(), store state when saving
        if self.GameState.MetadataCurrent.RandomState in [{}, None]: #if fresh map and thus no random state
            seed = None
            for hashtag in self.GameState.MetadataInitial.Hashtags:
                if hashtag.startswith("RNG"):
                    seed = int(hashtag[3:])
                    break
            if seed != None:
                self.rng = np.random.default_rng(seed)
            else:
                self.rng = np.random.default_rng()
        else:
            self.rng = np.random.default_rng()
            self.rng.bit_generator.state = self.GameState.MetadataCurrent.RandomState

        #some hashtag handling... they're probably all special though
        #ugh GameData is frozen, otherwise I'd replace all the repair abilities with 0 - not possible
        if "NOREPAIR" in self.GameState.MetadataInitial.Hashtags:
            out = copy.deepcopy(self.GameData.UnitAbilities)
            for u, _ in enumerate(self.GameData.Units):
                out[(u, gc.REPAIR, gc.RECORDEXISTS)] = 0 #7 is the ability number for repair
            self.GameData = replace(self.GameData, UnitAbilities = out)

        #things we will do periodically anyway
        self.availableActions: list[clsAction] = []
        self.buildHelperArrays()
        #maybe an np array of shape (unit_index, 9 or so) for all the unit properties - not a ton faster than individual arrays
    def buildHelperArrays(self):
        #builds all helpers arrays which are derivable from the lightweight game state and game data
        #these are to help with speed, not sure if they all actually help though
        #either do surgical changes or call then when actions taken
        
        #i dont think we call often, but could not make freash but edit?
        self.unitDefenses = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.int8) #(unit normal defense + submerged bonus) + terrain bonus
        self.unitMobility = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.uint8) #just looking it up based on altitude
        self.unitAttackrangemin = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.uint8) #just looking it up based on altitude
        self.unitAttackrangemax = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.uint8) #just looking it up based on altitude
        self.locUnits = np.full((self.GameState.Map.Map.shape[gc.X], self.GameState.Map.Map.shape[gc.Y], len(self.GameData.Altitudes)), 255, dtype = np.int8) #255 is the max of int8 and used as "nothing here"

        self.locZoc = np.zeros((self.GameState.Map.Map.shape[gc.X], self.GameState.Map.Map.shape[gc.Y], len(self.GameData.Altitudes)), dtype=np.bool_) #which locations are adjacent to enemy team of current turn

        for u, coords in enumerate(self.GameState.Units.UnitHexes):
            # UnitX = self.GameState.Units.UnitHexes[(u, gc.X)]
            # UnitY = self.GameState.Units.UnitHexes[(u, gc.Y)]
            UnitAlt = self.GameState.Units.UnitHexes[(u, gc.ALT)]
            UnitNum = self.GameState.Units.UnitNumbers[u]
            UnitDefense = self.GameData.UnitAltitudes[(UnitNum, coords[gc.ALT], gc.DEFENSE)]
            UnitUnittype = self.GameData.Units[(UnitNum, gc.UNITTYPENUMBER)]
            TerrainNum = self.GameState.Map.Map[(coords[gc.X], coords[gc.Y])]
            TerrainDef = self.GameData.UnittypeTerrains[(UnitUnittype, TerrainNum, gc.DEFENSEBONUS)]
            UnitMobility = self.GameData.UnitAltitudes[(UnitNum, UnitAlt, gc.MOBILITY)]
            UnitAttackrangemin = self.GameData.UnitAltitudes[(UnitNum, coords[gc.ALT], gc.ATTACKRANGEMIN)]
            UnitAttackrangemax = self.GameData.UnitAltitudes[(UnitNum, coords[gc.ALT], gc.ATTACKRANGEMAX)]

            self.locUnits[tuple(coords)] = u
            self.unitDefenses[u] = UnitDefense + TerrainDef
            self.unitMobility[u] = UnitMobility
            self.unitAttackrangemin[u] = UnitAttackrangemin
            self.unitAttackrangemax[u] = UnitAttackrangemax

    def getAvailableActions(self):
        #returns list of actions (with their move before and after included) available to all (current player) units
        availableActions: list[clsAction] = []
        for n, up in enumerate(self.GameState.Units.UnitPlayers):
            if up == self.GameState.MetadataCurrent.CurrentPlayer:
                availableActions.extend(self.getAvailableActionsUnit(n))
        self.availableActions = availableActions
        return availableActions
    def getAvailableActionsUnit(self, unit_index):
        #adds actions to self list (with their move before and after included) available to unit of given index

        #lookup unit number
        #get a list of all its active abilities - probably build in the loader (or elsewhere) this pre-built as one table
        #for the ones that involve movement, do pathing, attack selection, pathing if relevant

        availableActions: list[clsAction] = []

        unitnum = self.GameState.Units.UnitNumbers[unit_index]
        cp = self.GameState.MetadataCurrent.CurrentPlayer

        #initial moves dedup, use in both attack and plain move (and infect/assimilate/reprogram). Basically everything has move unless emp so no conditions on this
        initialMoves: list[tuple] = []
        initialMoves = self.getAvailableMoves(
            unit_index
            # , clsLoc(
            #     self.GameState.Units.UnitHexes[(unit_index, gc.X)]
            #     , self.GameState.Units.UnitHexes[(unit_index, gc.Y)]
            #     , self.GameState.Units.UnitHexes[(unit_index, gc.ALT)]
            #     )
            , self.GameState.Units.UnitHexes[(unit_index)]
            , self.unitMobility[unit_index]
            , None
            )

        for a, abilityrecord in enumerate(self.GameData.UnitAbilities[unitnum]):
            if abilityrecord[gc.RECORDEXISTS] == 0: continue
            
            match a:
                case gc.ATTACK: #attack normally
                    #build action list (can edit later to add moveAfterAttack)
                    for iloc in initialMoves:
                        hexesInRange = self.getHexesInRange(
                            iloc[gc.X]
                            , iloc[gc.Y]
                            , self.unitAttackrangemin[unit_index]
                            , self.unitAttackrangemax[unit_index]
                            )
                        for hexE in hexesInRange:
                            for alt, _ in enumerate(self.GameData.Altitudes):
                                i = self.locUnits[(hexE[gc.X], hexE[gc.Y], alt)]
                                if i in (255, -1): continue
                                up = self.GameState.Units.UnitPlayers[i]
                                if up == cp: continue
                                availableActions.append(clsAction(
                                    unit_index
                                    , a #ability number=attack
                                    , iloc
                                    , i #enemy
                                    , iloc
                                ))
                    #does it have move after attack?
                    if self.GameData.UnitAbilities[(unitnum, gc.MOVEAFTERATTACK, gc.RECORDEXISTS)] == 1:
                        afterMobility = self.GameData.UnitAbilities[(unitnum, gc.MOVEAFTERATTACK, gc.ABILITYSTRENGTH)]
                        #split for all move after attack
                        for action in availableActions:
                            #CALCULATE HERE IF ENEMY DIES
                            defenderDeadIndex = None
                            rngState = self.rng.bit_generator.state
                            ahp, dhp, _ = self.calcAttack(unit_index, action.BeforeAttackLoc, 0, action.DefenderUnitIndex)
                            if ahp == 0: continue #attacker dead, no move after attack
                            if dhp == 0: defenderDeadIndex = action.DefenderUnitIndex
                            #now find moves
                            afterMoves: list[clsLoc] = []
                            afterMoves = self.getAvailableMoves(
                                unit_index
                                , action.BeforeAttackLoc
                                , afterMobility
                                , defenderDeadIndex
                                )
                            #for each after move, create new action option
                            for afterMove in afterMoves:
                                if afterMove != action.AfterAttackLoc:
                                    newaction = copy.deepcopy(action)
                                    newaction.AfterAttackLoc = afterMove
                                    availableActions.append(newaction)
                case gc.REPAIR: #repair
                    pass
                case gc.MOVE: #just move
                    #create available actions
                    for iloc in initialMoves:
                        availableActions.append(clsAction(
                            unit_index
                            , a #ability number=attack
                            , iloc
                            , 255 #no enemy
                            , iloc
                            ))
                case gc.PASSTURN: #PassTurn - let's not include this so AI more effecient, should be separate output node maybe??
                    pass 

        return availableActions
    def getAvailableMoves(self, unit_index, start_loc: np.ndarray, mobility, dead_unit_index = None) -> set[tuple]:
        #this can be called on the moveAfterAttack, so unit data will not be of its start movement position
        #start hex tuple is (x, y, state), get the unit type from unit_index
        #returns valid destination... tuples. We assume same altitude... but including it slows us down

        #aware of ZOC, but not disabled
        #does not include friendly occupied spaces

        #PLAN
        #get movement total
        #breadth first

        adjacentIncs = [(-1, 1), (0, 1), (-1, 0), (1, 0), (0, -1), (1, -1)]

        #add starting because we can attack without moving. This does technically now allow moving and not attacking nowhere and thus skipping healing...
        unitnum = self.GameState.Units.UnitNumbers[unit_index]
        pq = [(0, start_loc)] #list of hexes to explore
        best = {tuple(start_loc): 0}
        reachableLocs: set[tuple] = set() #we will end up adding the starting loc
        # reachableLocs: set[clsLoc] = set() #we will end up adding the starting loc
        # reachableLocs: list[np.ndarray] = list() #np.ndarray because we assume those are faster than the dataclasses, and list because np.ndarrays are not hashable

        while pq: #while list of unexplored nodes
            accum_cost, loc = heapq.heappop(pq)

            # #eh, prefer this in the adj loop?
            # if cost > mobility: continue

            #look at adjacents
            for inc in adjacentIncs:
                #coords and OOB
                x = loc[gc.X] + inc[gc.X]
                y = loc[gc.Y] + inc[gc.Y]
                if x >= self.GameState.Map.Map.shape[0] or x < 0 or y >= self.GameState.Map.Map.shape[1] or y < 0: continue #OOB
                new_loc = (x, y, start_loc[gc.ALT])

                #unit here?
                friendlyOccupied = False
                i = self.locUnits[(x, y, start_loc[gc.ALT])]
                if i not in [255, -1, None, dead_unit_index]:
                    cp = self.GameState.MetadataCurrent.CurrentPlayer
                    ct = self.GameState.MetadataInitial.PlayersInitial[cp].Team
                    ip = self.GameState.Units.UnitPlayers[i]
                    it = self.GameState.MetadataInitial.PlayersInitial[ip].Team
                    if ct != it: continue #enemy unit, can't move here. Normally code can't get here due to zoc but maybe emp or something
                    friendlyOccupied = True

                #terrain cost
                terrainNum = self.GameState.Map.Map[(x, y)]
                inc_cost = self.GameData.UnitTerrains[(unitnum, terrainNum, gc.MOBILITYCOST)]
                if inc_cost in [0, -1, None]: continue #movement not allowed
                new_cost = accum_cost + inc_cost
                if new_cost > mobility: continue #movement too costly

                if new_cost >= best.get(new_loc, float('inf')): continue #ignore backtracking or equivalent paths
                
                #check adjacent enemy ZOC (should stop us from moving onto enemy too)
                if dead_unit_index is None:
                    zoc = self.locZoc[new_loc]
                else: #alternate manual method, only needed if locZoc invalid due to dead enemy
                    zoc = False
                    for einc in adjacentIncs: #check everything around this planned hex
                        ex = x + einc[0]
                        ey = y + einc[1]
                        ei = self.locUnits[(ex, ey, start_loc.Altitude)]
                        if ei in [255, None]: continue
                        cp = self.GameState.MetadataCurrent.CurrentPlayer
                        ct = self.GameState.MetadataInitial.PlayersInitial[cp].Team
                        ep = self.GameState.Units.UnitPlayers[ei]
                        et = self.GameState.MetadataInitial.PlayersInitial[ep].Team
                        if ct != et:
                            zoc = True
                            break
                
                #if we have more we can go (and this is fresh or best), add this new location to list to exxplore
                if zoc == False and new_cost < mobility and new_cost < best.get(new_loc, float('inf')): 
                    best[new_loc] = new_cost #assign or improve          
                    heapq.heappush(pq, (new_cost, new_loc))
                    if friendlyOccupied == False and new_loc not in reachableLocs: #only add to reachable if not occupied. Reachable will be slightly smaller list than best
                        reachableLocs.add(new_loc)
                
        return reachableLocs #set of locs

    
    def getAdjacentLocs(self, originLoc: clsLoc) -> list[clsLoc]:
        #return all adjacent locs (with map borders in mind)

        adjacentIncs = [(-1, 1), (0, 1), (-1, 0), (1, 0), (0, -1), (1, -1)]
        adjacentLocs: list[clsLoc] = []

        for inc in adjacentIncs:
            x = clsLoc.X + inc[0]
            y = clsLoc.Y + inc[1]
            if x >= self.GameState.Map.Map.shape[0] or y >= self.GameState.Map.Map.shape[1]: continue #OOB
            adjacentLocs.append(clsLoc(x, y, gc.DEFAULTALTITUDE))
        
        return self.getAdjacentLocs
            
    
    def calcAttack(self, au, aloc: clsLoc, popupBonus, du):
        #calculate result of an attack (resulting hps... add conditions (plague) later)
        #au = attacking index
        #aloc = attacking location
        #du = defender index
        #popupBonus = popup. Actually everything else (veterancy, GUB) I think I'll handle in here?

        #returns (ahp, dhp, plague or other weird stuff)

        #nonuniform non-else dependent info
        attackerUnitIndex = au
        defenderUnitIndex = du
        attackerX = aloc.X
        defenderX = self.GameState.Units.UnitHexes[(defenderUnitIndex, gc.X)]
        attackerY = aloc.Y
        defenderY = self.GameState.Units.UnitHexes[(defenderUnitIndex, gc.Y)]
        attackerAltitude = aloc.Altitude
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
        popupBonus = popupBonus
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
                + 0.05*(popupBonus + gangupBonus)
                - 0.05*defenderDefenseTotal
                + 0.05*(math.floor(attackerArmorpiercing*defenderDefenseTotal*5)/5) #round down to nearest 0.2 (before multiply by 0.05)
                )
            damage = self.calcDamage(attackerUnitHp, attackerP)
            dhp = max(0, defenderUnitHp - damage)
            

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
            ahp = max(0, attackerUnitHp - damage)

        return (ahp, dhp, None)
    def calcDamage(self, h, p): #should be the only thing that calls the rng.random()

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
                if self.rng.random() <= p:
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
    def getHexesInRange(self, x0, y0, dist_min: int, dist_max: int):
        #returns list of (x, y) tuples that are within dist_min and dist_max of the origin x0, y0
        results = []

        dmax = int(dist_max) #because sometimes we are getting passed unsigned ints and neg goes to 255 or whatever #RuntimeWarning: overflow encountered in scalar negative
        # Search bounding box: axial hex distance never exceeds Manhattan bounds
        for dx in range(-dmax, dmax+1): 
            for dy in range(-dmax, dmax+1):
                x = x0 + dx
                y = y0 + dy

                if x >= self.GameState.Map.Map.shape[0] or x < 0 or y >= self.GameState.Map.Map.shape[1] or y < 0:
                    continue

                d = self.getDist(x0, y0, x, y)
                if dist_min <= d <= dist_max:
                    results.append((x, y))

        return results
    
    def applyAction(self, action: clsAction):
        #what is the form of the action?
            #unit index, active ability number perhaps, move to xy, attack unit index, final position xystate
        
        #validate action is in list of actions
        
        #do we put all the abilities in here, or in separate file?

        print(f"Applying action: {action}")

        if action not in self.availableActions:
            raise RuntimeError(f"Action not in available list. Action: {action}")

        match action.AbilityNumber:
            case gc.ATTACK: #attack
                #? validate it can move there and there is a target (and target in range)
                    # current hex = self.GameState.Units.UnitHexes(action.UnitIndex)
                attackerDead = False

                ahp, dhp, plagueStuff = self.calcAttack(action.UnitIndex, action.BeforeAttackLoc, 0, action.DefenderUnitIndex)

                #attacker damage inflicted
                if dhp == 0:
                    self.destroyUnit(action.DefenderUnitIndex)
                    #let the system know there's a new space open for movement and no ZOC
                else:
                    self.GameState.Units.UnitHps[action.DefenderUnitIndex] = dhp

                #reciprocal damage
                #do it
                if ahp == 0:
                    self.destroyUnit(action.UnitIndex)
                    attackerDead = True
                    #if unit destroyed... no move after attack. We know that due to available actions... hm
                else:
                    self.GameState.Units.UnitHps[action.UnitIndex] = ahp

                #update it's position
                if attackerDead == False:
                    self.GameState.Units.UnitHexes[action.UnitIndex] = [action.AfterAttackLoc.X, action.AfterAttackLoc.Y, action.AfterAttackLoc.Altitude]

            case gc.MOVE: #move 
                #validate it can move there
                pass
            case gc.REPAIR: #repair
                #we have disabled this from hashtags by modifying GaemData
                #if repairing is disabled, this should not be called
                pass
        
        # print(self.GameState.Units.UnitHexes)
        # print(self.GameState.Units.UnitHps)
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
    def passTurn(self):
        #alter metadata passing turn
        #generate more rng
        #could put this in the ability file
        pass

# initialState = GameState(metadataInitial=None, map=None, metadataCurrent=None, units=GameUnits(unitNumbers=np.zeroes(10, dtype=np.int8), unitHps=None, unitTiles=None, tileUnits=None))
# print(initialState.units.unitHps)
# myEngine = Engine("stuff")

