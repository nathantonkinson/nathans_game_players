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
from dataclasses import replace, fields
import copy
import heapq #used for movement

import src.data.gameDataClasses as dc
from src.data.gameDataClasses import clsGameState, clsGameData, clsAction, clsLoc
import src.data.generated_constants as gc
import src.errorHandler as eh

ADJACENT_INCS = [(-1, 1), (0, 1), (-1, 0), (1, 0), (0, -1), (1, -1)]

class Engine:
    def __init__(self, gamestate: clsGameState, gamedata: clsGameData):

        #GameState and GameData
        self.GameState: clsGameState = gamestate #is a GameState data class
            #might need to make this private somehow and expose function only? for FOW 
        #probably read rule configs from game state? maybe not
        self.GameData: clsGameData = gamedata

        self.Initialization()

    def Initialization(self):

        #Gamestate should come with filled in races if sent from game manager (who will pick player preferred races)
        for player in self.GameState.MetadataInitial.PlayersInitial:
            if player.Race in (None, 255, -1, 0):
                player.Race = np.random.randint(1, len(self.GameData.Races_Name)) #not inclusive of high, so this is 1-3 because len=4

        #base player
        #this would be relevant if we didn't force the yaml user to fully copy the map
        # self.basenum = np.sum(np.isin(self.GameState.Map.Map, (2, 15))) #count bases
        # if self.GameState.Map.BasePlayers is None:
        #     # self.GameState.Map.BasePlayers = np.zeros(self.GameState.Map.Map.shape, dtype=np.uint8)
        #     pass
        # # elif self.GameState.Map.BasePlayers.shape:

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
        #NO REPAIR
        #ugh GameData is frozen, otherwise I'd replace all the repair abilities with 0 - not possible
        if "NOREPAIR" in self.GameState.MetadataInitial.Hashtags:
            out = copy.deepcopy(self.GameData.UnitAbilities)
            for u, _ in enumerate(self.GameData.Units):
                out[(u, gc.REPAIR, gc.RECORDEXISTS)] = 0 #7 is the ability number for repair
            self.GameData = replace(self.GameData, UnitAbilities = out) #beware this returns new instance
        #Roundlimit
        self.roundlimit = None
        roundlimithashtag: str = next((s for s in self.GameState.MetadataInitial.Hashtags if s.startswith("ROUNDLIMIT")), None)
        if roundlimithashtag is not None:
            self.roundlimit = int(roundlimithashtag[len("ROUNDLIMIT")+1:])


        #things we will do periodically anyway
        self.buildHelperArrays() 
            #maybe an np array of shape (unit_index, 9 or so) for all the unit properties - not a ton faster than individual arrays
        self.availableActions: list[clsAction] = [] #clsAction not hashable otherwise we'd do a set
        self.getAvailableActions()
        
    def buildHelperArrays(self):
        #builds all helpers arrays which are derivable from the lightweight game state and game data
        #these are to help with speed, not sure if they all actually help though
        #either do surgical changes or call then when actions taken
        
        cp = self.GameState.MetadataCurrent.CurrentPlayer
        ct = self.GameState.MetadataInitial.PlayersInitial[cp].Team

        #i dont think we call often, but could not make freash but edit?
        self.unitDefenses = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.int8) #(unit normal defense + submerged bonus) + terrain bonus
        self.unitMobility = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.uint8) #just looking it up based on altitude
        self.unitAttackrangemin = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.uint8) #just looking it up based on altitude
        self.unitAttackrangemax = np.zeros(len(self.GameState.Units.UnitNumbers), dtype = np.uint8) #just looking it up based on altitude
        self.locUnits = np.full((self.GameState.Map.Map.shape[gc.X], self.GameState.Map.Map.shape[gc.Y], len(self.GameData.Altitudes)), 255, dtype = np.int8) #255 is the max of int8 and used as "nothing here"

        self.locZoc = np.full((self.GameState.Map.Map.shape[gc.X], self.GameState.Map.Map.shape[gc.Y], len(self.GameData.Altitudes)), False, dtype=np.bool_) #which locations are adjacent to enemy team of current turn

        for u, coords in enumerate(self.GameState.Units.UnitHexes):
            # UnitX = self.GameState.Units.UnitHexes[(u, gc.X)]
            # UnitY = self.GameState.Units.UnitHexes[(u, gc.Y)]
            UnitAlt = self.GameState.Units.UnitHexes[(u, gc.ALT)]
            UnitNum = self.GameState.Units.UnitNumbers[u]
            if UnitNum in (0, 255, -1, None): continue
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

            #locZoc
            up = self.GameState.Units.UnitPlayers[u]
            ut = self.GameState.MetadataInitial.PlayersInitial[up].Team
            if ct != ut:
                for hex in self.getHexesInRange(coords[gc.X], coords[gc.Y], 1, 1):
                    self.locZoc[hex[gc.X], hex[gc.Y], coords[gc.ALT]] = True

    def getAvailableActions(self):
        #returns list of actions (with their move before and after included) available to all (current player) units
        availableActions: list[clsAction] = []
        for n, up in enumerate(self.GameState.Units.UnitPlayers):
            if up == self.GameState.MetadataCurrent.CurrentPlayer and self.GameState.Units.UnitActions[n] > 0:
                availableActions.extend(self.getAvailableActionsUnit(n))

        #special actions (pass turn, surrender)
        availableActions.append(clsAction(255, gc.PASSTURN, (0,0,gc.DEFAULTALTITUDE), 255, (0,0, gc.DEFAULTALTITUDE)))
        availableActions.append(clsAction(255, gc.SURRENDER, (0,0,gc.DEFAULTALTITUDE), 255, (0,0, gc.DEFAULTALTITUDE)))

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
                                if self.GameData.UnitAltitudes[(unitnum, alt, gc.RECORDEXISTS)] == 0: continue #skip if cannot attack this altitude
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
                            self.rng.bit_generator.state = rngState
                            if ahp == 0: continue #attacker dead, no move after attack
                            if dhp == 0: defenderDeadIndex = action.DefenderUnitIndex
                            #now find moves
                            afterMoves: set[clsLoc] = {}
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
                        if np.array_equal(iloc, self.GameState.Units.UnitHexes[unit_index]): continue #do not allow moving 0 distance
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

        #add starting because we can attack without moving. This does technically now allow moving and not attacking nowhere and thus skipping healing...
        unitnum = self.GameState.Units.UnitNumbers[unit_index]
        pq = [(0, start_loc)] #list of hexes to explore
        best = {tuple(start_loc): 0}
        reachableLocs: set[tuple] = set()
            # reachableLocs: set[clsLoc] = set()
            # reachableLocs: list[np.ndarray] = list() #np.ndarray because we assume those are faster than the dataclasses, and list because np.ndarrays are not hashable
        reachableLocs.add(tuple(start_loc))

        while pq: #while list of unexplored nodes
            accum_cost, loc = heapq.heappop(pq)

            # #eh, prefer this in the adj loop?
            # if cost > mobility: continue

            #look at adjacents
            for inc in ADJACENT_INCS:
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

                #update best to prevent duplication
                if new_cost < best.get(new_loc, float('inf')): 
                    best[new_loc] = new_cost #assign or improve          
                    if zoc == False and new_cost < mobility: #only add to list if we can continue (no zoc and still have movement)
                        heapq.heappush(pq, (new_cost, new_loc))
                    if friendlyOccupied == False and new_loc not in reachableLocs: #only add to reachable if not occupied. Reachable will be slightly smaller list than best
                        reachableLocs.add(new_loc)
                
        return reachableLocs #set of locs
            
    def calcAttack(self, au, aloc: tuple, popupBonus, du):
        #calculate result of an attack (resulting hps... add conditions (plague) later)
        #au = attacking index
        #aloc = attacking location
        #du = defender index
        #popupBonus = popup. Actually everything else (veterancy, GUB) I think I'll handle in here?

        #returns (ahp, dhp, plague or other weird stuff)

        #nonuniform non-else dependent info
        attackerUnitIndex = au
        defenderUnitIndex = du
        attackerX = aloc[gc.X]
        defenderX = self.GameState.Units.UnitHexes[(defenderUnitIndex, gc.X)]
        attackerY = aloc[gc.Y]
        defenderY = self.GameState.Units.UnitHexes[(defenderUnitIndex, gc.Y)]
        attackerAltitude = aloc[gc.ALT]
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
        if dist == 255: raise RuntimeError(f"Dist 255. dist={dist}, distcalc={self.getDist(attackerX, attackerY, defenderX, defenderY)}, ax={attackerX}, ay={attackerY}, dx={defenderX}, dy={defenderY}")
        #check if defender can retaliate
        retaliation = False if (dist > defenderRangeMax or dist < defenderRangeMin) else True
        

        #attacker damage inflicted
        dhp = defenderUnitHp
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
        ahp = attackerUnitHp
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
        
        xdiff = int(x1)-int(x2)
        ydiff = int(y1)-int(y2)
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

        i = action.UnitIndex
        attackerDead = False
        #some checks that should pass if engine is working nicely
        if action not in self.availableActions:
            raise RuntimeError(f"Action not in available list. Action: {action}")
        if i not in (-1, 255, None):
            if self.GameState.Units.UnitActions[i] <= 0:
                raise RuntimeError(f"Calling an action for unit with no actions left. Action: {action}")

        match action.AbilityNumber:
            case gc.ATTACK: #attack
                #? validate it can move there and there is a target (and target in range)
                    # current hex = self.GameState.Units.UnitHexes(action.UnitIndex)
                attackerDead = False

                ahp, dhp, plagueStuff = self.calcAttack(action.UnitIndex, action.BeforeAttackLoc, 0, action.DefenderUnitIndex)

                #attacker damage inflicted
                if dhp == 0:
                    self.destroyUnit(action.DefenderUnitIndex, action.UnitIndex)
                    #let the system know there's a new space open for movement and no ZOC
                else:
                    self.GameState.Units.UnitHps[action.DefenderUnitIndex] = dhp

                #reciprocal damage
                #do it
                if ahp == 0:
                    self.destroyUnit(action.UnitIndex, action.DefenderUnitIndex) #do we count reciprocal damage towards that player? yes
                    attackerDead = True
                    #if unit destroyed... no move after attack. We know that due to available actions... hm
                else:
                    self.GameState.Units.UnitHps[action.UnitIndex] = ahp

                #update it's position
                if attackerDead == False:
                    self.GameState.Units.UnitHexes[action.UnitIndex] = [action.AfterAttackLoc[gc.X], action.AfterAttackLoc[gc.Y], action.AfterAttackLoc[gc.ALT]]
            case gc.MOVE: #move 
                self.GameState.Units.UnitHexes[action.UnitIndex] = [action.AfterAttackLoc[gc.X], action.AfterAttackLoc[gc.Y], action.AfterAttackLoc[gc.ALT]]
            case gc.REPAIR: #repair
                #we have disabled this from hashtags by modifying GaemData
                #if repairing is disabled, this should not be called
                self.repairUnit(action.UnitIndex)
            case gc.PASSTURN:
                self.passTurn()
                return #no need to do the other stuff (I mean I guess wincon checking?? would only be useful if we killed our own unit)
            case gc.SURRENDER: #for the moment just sets winnerTeam to some else team
                #idk how I'd handle this with more than 2 teams, I guess pass player control to a bot
                #for the moment, set winning team to first team that is not ours
                cp = self.GameState.MetadataCurrent.CurrentPlayer
                ct = self.GameState.MetadataInitial.PlayersInitial[cp].Team
                for p, player in enumerate(self.GameState.MetadataInitial.PlayersInitial):
                    if player.Team != ct:
                        self.GameState.MetadataCurrent.WinnerTeam = player.Team
                        break
                return #no need for the other stuff

        #if win, return that
        if self.checkWinCon() == True: #wincon checks all teams and sets the winning gamestate
            return      

        if attackerDead == False:
            #decrement the acting units actions (could go before all the results but eh)
            if i not in (-1, 255, None):
                self.GameState.Units.UnitActions[i] -= 1

        #remove action (unneeded if full availableAction recalc but w/e)
        if action in self.availableActions: self.availableActions.remove(action)
        #if actions for the unit are now 0, remove all available actions for that unit
        if i not in [255, -1, None]:
            if self.GameState.Units.UnitActions[i] <= 0:
                for a in self.availableActions:
                    if a.UnitIndex == i:
                        self.availableActions.remove(a)

        #these are much more easily surgically altered, but also don't cost too much
        self.buildHelperArrays()
        #update available actions
        self.getAvailableActions()
        #There is maybe opportunity to not recalc available actions. 
            #It should not be crazy difficult in user-interaction speed (I hope) to full recalc. And if each turn there are 10 available actions, and thus AI is splitting like that, then 10x cost will be copying rather than this operation
            #To a human, recalc not needed much. But, things have changed:
                #Rng - unless deterministic
                #Enemy hp - affects move after attack
                #Enemy ZOC
                #Friendly positions
        #friendlies only - when generating abilities, disable action by some flag if occupied by friendly
            #upon action there is an origin (now empty) and dest (now full)
                #if origin = either of the two attack locations (and the other location is currently empty), enable it
                #if dest = either of the two attack locations, disable it
        #when generating abilities, disable action by some flag if ZOC or occupied but still make it
            #we need some flag on the action for what unit prevents? but multiple units could prevent??
    def destroyUnit(self, unit_index, attacker_index):
        #record kill count
        #delete unit
        #newly created units can take the slot later
        #let the system know there's a new space open for movement and no ZOC
        
        #record kill count
        ap = self.GameState.Units.UnitPlayers[attacker_index]
        dn = self.GameState.Units.UnitNumbers[unit_index]
        dv = self.GameData.Units[(dn, gc.COST)]
        self.GameState.MetadataCurrent.PlayersKills[ap] += dv

        #zero out the info of dead unit
        self.GameState.Units.UnitHps[unit_index] = 0
        self.GameState.Units.UnitNumbers[unit_index] = 0
        self.GameState.Units.UnitPlayers[unit_index] = 0 #players indexed at 1
        self.GameState.Units.UnitHexes[unit_index, :] = 0 #x, y, and altitude
        self.GameState.Units.UnitActions[unit_index] = 0
        #other properties like plauge, cooldown, exp, etc
    def repairUnit(self, unit_index):
        #check for medical tiles and nearby same player (not team) healer units

        #hp max
        hp_max = 10
        #veterancy
        eh.warning("Veterancy not accounted for in healing")
        current_hp = self.GameState.Units.UnitHps[unit_index]
        if current_hp == hp_max: return #if already at max, do nothing

        #start with units innate facotr
        unitnum = self.GameState.Units.UnitNumbers[unit_index]
        unitrepair = self.GameData.Units[(unitnum, gc.REPAIRRATE)]
        if unitrepair == 0: return #it can't heal
        totalrepair = unitrepair

        #check medical tile underneath
        loc = self.GameState.Units.UnitHexes[unit_index]
        terrainnum = self.GameState.Map.Map[loc[gc.X], loc[gc.Y]]
        if terrainnum == gc.MEDICAL:
            totalrepair *= 3

        #check nearby units for having healing ability
        for inc in ADJACENT_INCS:
            #coords and OOB
            x = loc[gc.X] + inc[gc.X]
            y = loc[gc.Y] + inc[gc.Y]
            if x >= self.GameState.Map.Map.shape[0] or x < 0 or y >= self.GameState.Map.Map.shape[1] or y < 0: continue #OOB

            #any units here?
            for a in self.GameData.Altitudes:
                if a == 0: continue
                i = self.locUnits[(x, y, a)]
                if i not in [255, -1, None]:
                    cp = self.GameState.MetadataCurrent.CurrentPlayer
                    ip = self.GameState.Units.UnitPlayers[i]
                    if cp != ip: continue #not same player unit, not helpful
                    inum = self.GameState.Units.UnitNumbers[i]
                    #check if that unit has repairboost
                    if self.GameData.UnitAbilities[(inum, gc.REPAIRBOOST, gc.RECORDEXISTS)] == 1:
                        totalrepair *= self.GameData.UnitAbilities[(inum, gc.REPAIRBOOST, gc.ABILITYSTRENGTH)]
                        continue

        #actually do repair
        self.GameState.Units.UnitHps[unit_index] = min(hp_max, current_hp + totalrepair)
    def passTurn(self):
            #pass turn
            
            #heal units that still have actions
            if "NOREPAIR" not in self.GameState.MetadataInitial.Hashtags:
                cp = self.GameState.MetadataCurrent.CurrentPlayer
                for u, p in enumerate(self.GameState.Units.UnitPlayers):
                    if p != cp: continue
                    for _ in range(self.GameState.Units.UnitActions[u]):
                        self.repairUnit(u)
                    self.GameState.Units.UnitActions[u] = 0
    
            #cycle current player and round
            cp = (self.GameState.MetadataCurrent.CurrentPlayer + 1) % len(self.GameState.MetadataInitial.PlayersInitial)
            self.GameState.MetadataCurrent.CurrentPlayer = cp
            if self.GameState.MetadataCurrent.CurrentPlayer == 0:
                self.GameState.MetadataCurrent.Round += 1
            #check wincon in case the person killed themselves on their turn and made themselves lose
            if self.checkWinCon() == True: #duplication of wincon checking at end of action
                cp = self.GameState.MetadataCurrent.CurrentPlayer
                ct = self.GameState.MetadataInitial.PlayersInitial[cp].Team
                self.GameState.MetadataCurrent.WinnerTeam = ct
                return
            #check round limit
            if self.roundlimit not in [0, -1, None]:
                if self.GameState.MetadataCurrent.Round > self.roundlimit:
                    #call some kind of heuristic
                    pass
            #refresh the actions of current player units
            for u, p in enumerate(self.GameState.Units.UnitPlayers):
                if p == cp:
                    #lookup actions for that unit
                    un = self.GameState.Units.UnitNumbers[u]
                    ua = self.GameData.Units[(un, gc.ACTIONSPERTURN)]
                    self.GameState.Units.UnitActions[u] = ua
    
            self.buildHelperArrays()
            self.getAvailableActions()

    def checkWinCon(self):
        #checks if any team has won
        #currently running this at end of every action, but could maybe do it less.

        def checkBases():
            #find all bases, and check either our team owns or we're sitting on them
            # self.basenum = np.sum(np.isin(self.GameState.Map.Map, (2, 15))) #count bases
            for x, row in enumerate(self.GameState.Map.Map):
                for y, terrainNum in enumerate(row):
                    if terrainNum in (gc.HARBOR, gc.BASE):
                        #check ownership
                        bp = self.GameState.Map.BasePlayers[(x, y)]
                        if bp in (-1, 255, None): continue #no one owns it, check next
                        bt = self.GameState.MetadataInitial.PlayersInitial[bp].Team
                        if bt == t: continue #current team already owns it, check next
                        #check sitting
                        i = self.locUnits[(x, y, gc.DEFAULTALTITUDE)]
                        if i in (-1, 255, None): return False #enemy owned and no unit there
                        sp = self.GameState.Units.UnitPlayers[i]
                        st = self.GameState.MetadataInitial.PlayersInitial[sp].Team
                        if st == t: continue #current team sitting on base, check next
                        return False #enemy owned and enemy unit there
            #all checks passed
            return True
        
        def checkUnits():
            #check no enemy units left
            for up in self.GameState.Units.UnitPlayers:
                if up in [255, -1, None]: continue
                ut = self.GameState.MetadataInitial.PlayersInitial[up].Team
                if ut != t: return False
            return True

        #check through all teams
        checked_teams = []
        for p, _ in enumerate(self.GameState.MetadataInitial.PlayersInitial):
            t = self.GameState.MetadataInitial.PlayersInitial[p].Team
            if t in checked_teams: continue
            checked_teams.append(t)

            match self.GameState.MetadataInitial.WinCon:
                case 1: #capture enemy bases
                    win = checkBases()
                case 2:
                    win = checkUnits()
                case 3:
                    win = checkBases() and checkUnits()

            if win:
                self.GameState.MetadataCurrent.WinnerTeam = t
                return True

        return False
        
# initialState = clsGameState(metadataInitial=None, map=None, metadataCurrent=None, units=GameUnits(unitNumbers=np.zeroes(10, dtype=np.int8), unitHps=None, unitTiles=None, tileUnits=None))
# print(initialState.units.unitHps)
# myEngine = Engine("stuff")

