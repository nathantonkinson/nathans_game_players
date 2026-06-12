import sys
import math
import copy
import time
from collections import Counter

# To debug: print("Debug messages...", file=sys.stderr, flush=True)
# seems to tolerate 1 but not 2 seconds of delay, at all stages of nitialization and play
# It has limitations on how much you can debug print (then says ran out of time, I think, and does...)
# Can use try: except: to isolate print debug on runtime errors

#region TO DO
#could add backwards from bottom (but doesn't work well for huge maze, unless allowed to do that with infinite time before call first position)
#could add self timer to not exceed the 1 second
#could add keep looking for paths until done looking or find exit (don't stop at mere depth)
#could save 0 (neutral result) paths and just build on them or something
#check minimal rotations first
#we are ignoring a situation where new rock added to existing solved plan collides with another rock before that other rock collides with a third, letting the 3rd kill us
#put indy in the entity list
#endregion

#region TWO ROCKS COLLIDE
#1) At each step, split for all combinations of rotations of entities (rocks and indy). This might balloon too much. It could pair well with a self-time limiter
    #Layer 1 = board state incrementer, then calls rotator with entity list
    #Layer 2 = rotator checks all rotations of entity[0], then calls rotator again for next entity in list. If last, calls board state recursive
    #problems with extreme banking/back updating
#2) Run all possible paths of each entity separately. Then look for intersections. Not sure if this is computationally better than #1)
    #Get jagged list of paths lists, one path list per entity
    #Intersections
        #option a) for each path, make list of intersections with each other path. Seems a little intense, we're at 4 lists deep now
        #option b) step through time on all paths simulataneously. Look for intersections between different entities. Alternatively step through grid locations
    #... we need to find a selection of entity paths where any indy intersections occur below other intersections
#3) At each step, choose a rotation from among all entities, including doing nothing (and banking a rotation). Allow combos of rotations up to bank
    #problem with banks affecting upstream intersections with other entities
#4) At each step, choose left or right along simulated path of any entity (beyond its current, and including the death square to allow passage)
    #only terminate recursive on immediate death of Indy
    #I guess we do technically need to recalc what happens after every rotation... ugh
    #potential for checking a lot of garbage if open paths are long, but perhaps less than the crazy combinatorics of the others
    #I think only checking along path should be valid. No use in modifying else square before opening up the kill square
    #include do nothing
    #save time by...
        #record failing rotation lists. Maybe can do more recording than that, since we really are searching all rotation lists, so might not help
        #rotations must be made in order of effect. If you do a rotation in a path, do not in a later step affect higher up the path
        #you also cannot make rotations after indys death point
        #if entity paths overlap (not at same time, that would be collisions) don't duplicate cells
#endregion

#entities can get to the same space via different ways and at different times
#entities cannot visit same space twice in one path


#avoid copy.deepcopy() on board
# if no paths cross, can we try to eliminate (not do the work for) duplicate paths with identical cells but different (often redundant) rotations?
# do depth=5 e.g., then check time (or not), maybe check if all start the same way, then next iteration build on the valid_paths to depth+5 beyond the original
#     perhaps this way we can save compute
#change max depth to affect the recursive, not run path
#switch maybe to a more global time index, maybe add that to path info

#we can do some more dedup on valid paths before next segment... or inside the recursive
    #if at any point the board is the same and all entities have the same position and entries, is duplicate
    #we want to remove rotations in different sequences
    #remove rotations in backwards direction or something that don't affect entities


room_types = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
entry_types = ["TOP", "LEFT", "RIGHT"]

def debug(msg):
    logging = True
    if logging == True:
        print(msg, file=sys.stderr, flush=True)

class IndyPlayer():

    def __init__(self): #gets initial info
        
        #precompute before we even start the game
        self.nextRoomOffsets = dict() #key = (room type, entry type), values = (x increment, y increment, new_entry_type)
        self.nextRoomOffsetsPrecalc()

        #GET BOARD SETUP
        # w: number of columns.
        # h: number of rows.
        self.w, self.h = [int(i) for i in input().split()]
        self.board = []
        for i in range(self.h):
            self.board.append(list(map(int, input().split())))  # represents a line in the grid and contains W integers. Each integer represents one room of a given type.:
            print("\t".join(map(str, self.board[i])), file=sys.stderr, flush=True)
        # print(f"Board={self.board}", file=sys.stderr, flush=True)
        self.exit_x = int(input())  # the coordinate along the X axis of the exit (not useful for this first mission, but must be read).
        print(f"Exit x={self.exit_x}", file=sys.stderr, flush=True)
        self.board[self.h-1][self.exit_x] = -abs(self.board[self.h-1][self.exit_x]) #make exit unable to be rotated

        #PLANNING
        self.valid_paths = [] #a list of paths
        self.current_plan = [] #a list of steps (i.e. a path, the chosen plan from valid paths)
        self.found_win = False
        self.state_values = {} #key=((final path step (to get entity data)) + (board)), values=1,0,-1
        
        #ACTUALS ONLY
        self.path = [] #filled with dicts- x, y, room_type, entry, rotation_command, rock_info. First item is starting room, final is exit cell.
    def getCurrentInfo(self):
        inputs = input().split()
        self.xi = int(inputs[0])
        self.yi = int(inputs[1])
        self.entryi = inputs[2] #TOP, LEFT, or RIGHT
        print(f"Current position= {self.xi}, {self.yi}. Entering from={self.entryi}", file=sys.stderr, flush=True)
        self.r_num = int(input())  # the number of rocks currently in the grid.
        self.rock_info = []
        for _ in range(self.r_num):
            inputs = input().split()
            #list with entries [x, y, entry description]
            self.rock_info.append((int(inputs[0]), int(inputs[1]), inputs[2]))
        print(f"Rocks={self.rock_info}", file=sys.stderr, flush=True)

    def nextRoomOffset(self, room_type, entry_type): #returns 0, 0, TOP, or -1, -1 etc for movement  
        #technically we don't need to pass entry type since the offset would give you that, but w/e
        room_type = abs(room_type)
        if room_type == 0:
            pass
        elif room_type == 1:
            return 0, 1, "TOP"
        elif room_type in [2, 6]: #6 has entry from top but is not valid somehow
            if entry_type == "LEFT":
                return 1, 0, "LEFT"
            elif entry_type == "RIGHT":
                return -1, 0, "RIGHT"
        elif room_type == 3:
            if entry_type == "TOP":
                return 0, 1, "TOP"
        elif room_type == 4:
            if entry_type == "TOP":
                return -1, 0, "RIGHT"
            elif entry_type == "RIGHT":
                return 0, 1, "TOP"
        elif room_type == 5:
            if entry_type == "TOP":
                return 1, 0, "LEFT"
            elif entry_type == "LEFT":
                return 0, 1, "TOP"
        elif room_type == 7:
            if entry_type in ["TOP", "RIGHT"]:
                return 0, 1, "TOP"
        elif room_type == 8:
            if entry_type in ["LEFT", "RIGHT"]:
                return 0, 1, "TOP"
        elif room_type == 9:
            if entry_type in ["LEFT", "TOP"]:
                return 0, 1, "TOP"
        elif room_type == 10:
            if entry_type == "TOP":
                return -1, 0, "RIGHT"
        elif room_type == 11:
            if entry_type == "TOP":
                return 1, 0, "LEFT"
        elif room_type == 12:
            if entry_type == "RIGHT":
                return 0, 1, "TOP"
        elif room_type == 13:
            if entry_type == "LEFT":
                return 0, 1, "TOP"
        
        #didn't hit any of our conditions, is invalid
        return None, None, None  
    def nextRoomOffsetsPrecalc(self):
        for room_type in room_types:
            for entry_type in entry_types:
                self.nextRoomOffsets[(room_type, entry_type)] = self.nextRoomOffset(room_type, entry_type)
    def convertRoom(self, starting_room_type, rotation):
        try:
            starting_room_type = abs(starting_room_type)
            if starting_room_type < 0 or starting_room_type > 13:
                return None
            if rotation not in ["LEFT", "RIGHT"]:
                return None
        except:
            return None

        #listed in order of RIGHT (clockwise right hand positive) rotation
        t_rooms = [6, 7, 8, 9] 
        c_rooms = [10, 11, 12, 13]
        
        if starting_room_type == 0:
            return 0
        elif starting_room_type == 1:
            return 1
        elif starting_room_type == 2:
            return 3
        elif starting_room_type == 3:
            return 2
        elif starting_room_type == 4:
            return 5
        elif starting_room_type == 5:
            return 4
        elif starting_room_type in t_rooms:
            current_index = t_rooms.index(starting_room_type)
            increment = 1 if rotation == "RIGHT" else -1 
            current_index = (current_index + increment) % len(t_rooms)
            return t_rooms[current_index]
        elif starting_room_type in c_rooms:
            current_index = c_rooms.index(starting_room_type)
            increment = 1 if rotation == "RIGHT" else -1 
            current_index = (current_index + increment) % len(c_rooms)
            return c_rooms[current_index]
        
        print(f"Convert room failure", file=sys.stderr, flush=True)
        return None #shouldn't be able to get here

    def runPath(self, path, board, start_step_index, extra_depth): #complete but untested, sim from index write/overwrite
        #takes a path starting at step_index, takes starting conditions, and recalculates path of indy and rocks based on the rotation commands in the path
        #writes coords of entities in the wall if they run into wall, or in collision but not after
        #does not write coords for OOB, or row of indy OOB
        #truncates path such that final row is when indy dies by collision or wall, or next step is OOB

        #returns -1 for indy death (at any point. We put immediate death check in the recursive)
        #returns 0 for max depth
        #returns 1 for win
        
        step_index = start_step_index
        result = None

        while True: #exit on indy death or win

            while True: #do basic physics, fake loop to bail if indy is immediately dead
                death = True
                #calculate step, building info needed for next path line 
                prev = path[step_index]
                #prev entities
                entities = [(prev["x"], prev["y"], prev["entry"])]
                entities.extend(prev["rock_info"])
                #rotation
                if prev["rotation_command"] != []: #actually there shouldn't be rotation commands, except the one at first step, but let's leave this at each for multi-purpose
                    #shouldn't happen, but check the command is not same cell as an entity
                    if any(entity[0] == prev["rotation_command"][0] and entity[1] == prev["rotation_command"][1] for entity in entities): print("Trying to rotate where entities are")
                    board[prev["rotation_command"][1]][prev["rotation_command"][0]] = self.convertRoom(board[prev["rotation_command"][1]][prev["rotation_command"][0]], prev["rotation_command"][2])
                #indy movement
                xchange, ychange, ientry = self.nextRoomOffset(prev["room_type"], prev["entry"])
                # debug(f"runPath increment: {xchange}, {prev}")
                if xchange is None: break #indy is currently in invalid room rotation, cannot write next
                x = prev["x"]+xchange
                y = prev["y"]+ychange
                if not ((0 <= x <= self.w - 1) and (0 <= y <= self.h-1)): break #indy OOB, cannot write this
                #rock stuff
                rock_info = []
                # print(f"Calculating rock movement: Path = {path}, Prev rock info = {prev['rock_info']}", file=sys.stderr, flush=True)
                for rock in prev["rock_info"]:
                    writeNull = True
                    if rock != (None, None, None):
                        #check motion through current/prior room
                        xchange, ychange, rock_entry = self.nextRoomOffsets[(board[rock[1]][rock[0]], rock[2])]
                        if ((0 <= rock[0]+xchange <= self.w - 1) and (0 <= rock[1]+ychange <= self.h-1)): #rock stil inbounds
                            writeNull = False
                            rock_info.append((rock[0]+xchange, rock[1]+ychange, rock_entry)) #rock could still be doing collision, or entering invalid room, but current room is fine
                    if writeNull == True:
                        rock_info.append((None, None, None))
                
                #able to write line
                if len(path) - 1 == step_index: #writing new line
                    path.append({"x":x, "y":y, "room_type":board[y][x], "entry":ientry, "rotation_command":[], "rock_info":rock_info})
                else:
                    path[step_index+1] = {"x":x, "y":y, "room_type":board[y][x], "entry":ientry, "rotation_command":path[step_index+1]["rotation_command"], "rock_info":rock_info}

                #got here without break, so we wrote record
                death = False
                break

            if death == True: #in bad room (so no next) or going OOB
                result = -1
            #conditions that break us from loop (but still wrote line) - namely collisions
            #indy collision
            elif any(rock[0] == x and rock[1] == y for rock in rock_info): 
                result = -1 #indy collide with rock
            #check for win or max depth (valid path appending we do in the recursive)
            elif (y == self.h - 1 and x == self.exit_x): #proper exit
                result = 1
            elif step_index +1 >= self.max_depth + extra_depth:
                result = 0
            
            if death == False: step_index += 1

            # debug(f"runPath: step_index={step_index}, result={result}, death={death}, current step={path[step_index]}")
            if result != None:
                path[:] = path[:step_index+1] #truncate path since indy died or won or whatever, nothing useful after. path[:] = is needed to modify the list instead of make a new var
                # debug(f"Truncated path to: {path}")
                return result

            #made it to next loop
            #rock dual (or triple) annihilation, useful for next loop
            counts = Counter(rock_info)
            repeats = {rock for rock, c in counts.items() if c > 1}
            rock_info = [(None, None, None) if rock in repeats else rock for rock in rock_info]
            if len(path) - 1 > step_index: #if future path information is filled out, add any new rocks that might have appeared
                rock_info.extend(path[step_index]["rock_info"][len(rock_info)-1:])

            #no death or win or max depth, keep going
         
    def pathingRecursive(self, path, path_index, board, minimal_path_index, extra_depth): #complete but untested, the rotate along path code   
        #path_index = index at which we are making the rotation command
        #minimal_path_index = future rotations must be made at this index or farther

        #check death right now (or OOB next), if so return -1

        #for all points along the path of all entities (beyond minimal index and up to indy death)
            #for left or right
                #call path modification: -1 for death anywhere, 0 for max depth, 1 for win
                #if 1 - record winning path, return 1 (could technically keep looking for other win variations but let's not)
                #if 0 - record path... maybe keep going recursive if we can with the minimal index stuff
                #if -1 - call recursive

        debug(f"Recursive at: path_index={path_index}, minimal={minimal_path_index}, cur coords={path[path_index]['x']} {path[path_index]['y']}")

        key = str((path[path_index], board))
        if key in self.state_values:
            #we will clear out all value=0s between each recursive starter, or at minimum between each depth pulse
            debug("Hit a state reduction")
            return self.state_values[key]

        local_path = copy.deepcopy(path)
        # self.runPath(local_path, copy.deepcopy(board), path_index) #this would double-check our path is good
        current_step = local_path[path_index] #where we are making rotation decision, where indy is in simulation
        best_result = -1 #could not do this if we stick with first 0 path we find

        #the path passed to us is already simulated given current rotations, and includes coords for entities if they end in walls, and its final row is when indy dies (or step before OOB) (or wins, or max depth
        if len(path) - 1 <= path_index: #path does not continue, Indy dies right now or next step by OOB. And it's not a win or we wouldn't be calling this function
            return -1
        
        #we are not checking do nothing because runPath does that, essentially, and once we find win we stop going
        #all cells along all paths
        checked_cells = [] #dedup here
        for step_index in range(len(local_path)-1,  max(minimal_path_index-1, path_index+1-1), -1): #starting from end to avoid messing up good indy path. And so path alterations don't mess up earlier. path_index+1-1: -1 because not inclusive, +1 because we can't rotate where entities are currently
            # try:
            step = local_path[step_index] #we might need to do path deepcopy stuff. We are editing path as we try different things. We start from end but if entity paths overlap, might make a path shorter and this will throw exception
            # except:
            #     debug(f"step index problems: path_index={path_index}, minimal_path_index={minimal_path_index}, pathlen-1={len(path)-1} step_index={step_index}, current_step={current_step}, path={path[minimal_path_index:]}")
            #     print("abort")
            entities = [(step["x"], step["y"], step["entry"])]
            entities.extend(step["rock_info"])                  
            #for projected position of all entities
            for entity_index, entity in enumerate(entities):
                if entity == (None, None, None): continue
                if (entity[0], entity[1]) in checked_cells: continue #skip already checked cells if entity paths overlap
                checked_cells.append((entity[0], entity[1]))
                if board[entity[1]][entity[0]] <= 1: continue #skip unrotateable (or 0 and 1 which don't matter)
                if any(entity_index != else_entity_index and entity[0] == else_entity[0] and entity[1] == else_entity[1] for else_entity_index, else_entity in enumerate(entities)): continue #skip if another entity here now (so unrotateable)
                room_types_checked = []
                for direction in ["RIGHT", "LEFT"]:
                    #dedup identical room types (2/3 and 4/5)
                    new_room_type = self.convertRoom(board[entity[1]][entity[0]], direction)
                    if new_room_type in room_types_checked: continue
                    room_types_checked.append(new_room_type)
                    #how do we check that this is not reversing a previous rotation in a way that affects nothing? check if previous rotation on this AND no entities enter space between prev and this
                    redundant = False
                    if entity[0] == 4 and entity[1] == 1 and path_index == 1: debug(f"Hitting redundancy test: step_index={step_index}, local_path={local_path}")
                    for temp_step in range(step_index-1, -1, -1):
                        debug(f"got into loop: temp step={temp_step}, coord={entity[0]} {entity[1]}")
                        temp_entities = [(local_path[temp_step]["x"], local_path[temp_step]["y"], local_path[temp_step]["entry"])]
                        temp_entities.extend(local_path[temp_step]["rock_info"])
                        if any(temp_entity[0] == entity[0] and temp_entity[1] == entity[1] for temp_entity in temp_entities): break #entity crossed path with this, this is not redundant rotation
                        if local_path[temp_step]["rotation_command"] != []:
                            if local_path[temp_step]["rotation_command"][0] == entity[0] and local_path[temp_step]["rotation_command"][0] == entity[1]: #rotation on same square, got here so no cross path
                                debug("Found prior rotation on this")
                                if direction != local_path[temp_step]["rotation_command"][2]: redundant = True #the two counteracted each other
                                if new_room_type in [2, 3, 4, 5]: redundant = True #room types that become the same upon double-rotation
                    if redundant == True: continue

                    #fill out info
                    entity_type = "INDY" if entity_index == 0 else "ROCK"
                    current_step["rotation_command"] = [entity[0], entity[1], direction, step_index-1, entity_type]
                    # debug(f"Trying path: path_index={path_index}, step={step_index}, minimal={minimal_path_index}, current_step={current_step}")
                    path = copy.deepcopy(local_path)
                    result = self.runPath(path, copy.deepcopy(board), path_index, extra_depth) #from path index because it might inadvertently affect a different entity sooner
                    best_result = max(result, best_result)
                    if result == 1: #terminus win
                        self.valid_paths.append(copy.deepcopy(path))
                        debug("Logged valid path result = 1")
                        self.found_win = True
                        # return 1 #could look for alternate wins but we're not doing that
                    if result == 0: #terminus max depth
                        self.valid_paths.append(copy.deepcopy(path))
                        debug("Logged valid path result = 0")
                        # return 0 #alternatively could look for wins by earlier modifications
                    if result == -1:
                        #edit board
                        og_room = board[current_step["rotation_command"][1]][current_step["rotation_command"][0]]
                        board[current_step["rotation_command"][1]][current_step["rotation_command"][0]] = self.convertRoom(og_room, current_step["rotation_command"][2])
                        result = self.pathingRecursive(path, path_index+1, board, step_index, extra_depth)
                        board[current_step["rotation_command"][1]][current_step["rotation_command"][0]] = og_room #undo board change
                        best_result = max(result, best_result)
                        # if result in [0, 1]: return result #could look for alt wins or win by more modification but no. If death however, keep looing

        self.state_values[str((path[path_index], board))] = best_result #shuldn't have the rotation yet
        return best_result
                
    def playGame(self):

        self.do_printing = False
        # game loop
        while True:
            #get info and compare to plan (if plan exists)
            self.getCurrentInfo() #at top so we don't have to call it in init
            turn_start_time = time.time()
            self.path.append({"x":self.xi, "y":self.yi, "room_type":self.board[self.yi][self.xi], "entry":self.entryi, "rotation_command":[], "rock_info":self.rock_info})
            
            #if we had a plan, check if we're where we expected, and rocks as expected, and align rocks to prior if some died, and check for new rocks
            calculation_required = False if self.current_plan != [] else True
            if self.current_plan != []:
                p = self.current_plan[0]
                # print(f"Prior adjust: p={p}", file=sys.stderr, flush=True)
                # print(f"Diagnose ignore rock: plan[0]rockinfo={p['rock_info']}, self rock info={self.rock_info}", file=sys.stderr, flush=True)
                if self.xi != p["x"] or self.yi != p["y"] or self.entryi != p["entry"]:
                    print(f"Aborting: Indy at ({self.xi}, {self.yi}), expected at ({p['x']}, {p['y']})")
                #check rocks as expected
                if len([rock for rock in p["rock_info"] if rock not in self.rock_info and rock != (None, None, None)]) > 0: 
                    print(f"Aborting: Rocks not in expected places. step rock info={p['rock_info']}, actuals={self.rock_info}")
                
                new_rocks = [rock for rock in self.rock_info if rock not in p["rock_info"]]
                #reorder self rock info to match old
                if new_rocks != []: 
                    self.rock_info = p["rock_info"] + new_rocks
                    p["rock_info"] = self.rock_info[:] #setting it to a copy, just to be safe
                
                #check if new rocks require alteration to plan. Maybe only need this if expected win because we need to recalc if expect 0 anyway? But if we built in edge recalc only, then need this I guess?
                if new_rocks != []:
                    result = self.runPath([copy.deepcopy(self.path[0])], copy.deepcopy(self.board), 0, 100)
                    if result == -1:
                        calculation_required = True
                    if calculation_required == False:
                        print(f"New rocks don't interefere with plan", file=sys.stderr, flush=True)
                
                #if require recalculation, destroy current plan
                if calculation_required == True:
                    self.current_plan = []
                    self.cellEntryValues = {}
                    self.valid_paths = []
                #if result indeterminate, still need to do some calculation, but don't destroy memory
                if calculation_required == False and expected_result == 0:
                    calculation_required = True
            
            #calc
            debug(f"Recalc occurring?: recalc={calculation_required}")
            if calculation_required == True:
                expected_result = None
                self.found_path = False #do we even keep this?
                if self.valid_paths == []:
                    self.valid_paths = [self.path[0:1]] #only final index (still a list though)
                #already removed [0] on valid paths at end of previous
                debug(f"valid paths before: len={len(self.valid_paths)}")
                
                self.max_depth = 3 #this is increment, not full. Make separate var for full?? and/or control via time?
                
                #do chunks of max_depth exploration until win or run out of time
                while True:
                    valid_paths_iterable = copy.deepcopy(self.valid_paths)
                    self.valid_paths = []
                    # debug(f"Length of iterable: {len(valid_paths_iterable)}")
                    self.state_values = {k: v for k, v in self.state_values.items() if v != 0} #remove 0s from state values so we can recalc them deeper
                    for valid_path in valid_paths_iterable:
                        #plan
                            #run path to get board (path should all be same length if they are not wins)
                            #pass step without rotation, plus board
                            #take all newly added valid paths and append the start of the path to them
                        
                        # #check problems with prior valid paths
                        # if len(valid_path) != self.max_depth + 1 and valid_paths_iterable != [self.path[0:1]]:
                        #     debug(f"Valid path length issue: len={len(valid_path)}, max_depth={self.max_depth}+1, valid_paths={valid_paths_iterable}, first path as list={[self.path[0:1]]}")
                        #     raise RuntimeError("Required calc = true but valid path (assume 0) not len=max_depth... hm")
                        
                        #trim valid path down so its last entry is first with rotation command (allowing waits in between)
                        #also get minimal from 
                        last_rotation_index = None
                        minimal = None
                        for step_index in range(len(valid_path)-1, 1, -1):
                            if valid_path[step_index]["rotation_command"] != []: 
                                # valid_path = valid_path[:step_index+2]
                                last_rotation_index = step_index
                                break
                            if step_index == 0: #I guess path had no rotations in it, idk why
                                valid_path = valid_path[:1]
                                minimal = 0
                                break
                        if last_rotation_index != None:
                            #find index in the path that the final rotation affects to get minimal
                            for step_index in range(len(valid_path)-1, -1, -1):
                                entities = copy.deepcopy(valid_path[step_index]["rock_info"])
                                entities.append((valid_path[step_index]["x"], valid_path[step_index]["y"], valid_path[step_index]["entry"]))
                                # debug(f"Entities: last rot={last_rotation_index}, x={valid_path[last_rotation_index]['rotation_command'][0]}, y={valid_path[last_rotation_index]['rotation_command'][1]}, entites={entities}")
                                for entity in entities:
                                    if entity[0] == valid_path[last_rotation_index]["rotation_command"][0] and entity[1] == valid_path[last_rotation_index]["rotation_command"][1]:
                                        minimal = step_index - (last_rotation_index+1) #path is going to be trimmed to start at first non-rotation index (last rot+1), 
                                        valid_path = valid_path[:min(last_rotation_index+2, len(valid_path))] #+2 because it is like range, not inclusive, and we also want the final step that has no rotation command
                                        break
                                if minimal != None: break
                        if minimal == None and len(valid_path) == 1:
                            minimal = 0
                            last_rotation_index = -1 if valid_path[0]["rotation_command"] == [] else 0
                        debug(f"Trimmed valid path: minimal={minimal}, last rot={last_rotation_index}")
                        
                        #prep board
                        valid_path_board = copy.deepcopy(self.board)
                        for step in valid_path: #make board look like final path step. Final path step shouldn't have any rotation commands
                            if step["rotation_command"] != []:
                                valid_path_board[step["rotation_command"][1]][step["rotation_command"][0]] = self.convertRoom(valid_path_board[step["rotation_command"][1]][step["rotation_command"][0]], step["rotation_command"][2])
                        if valid_path[-1]["rotation_command"] != []: raise RuntimeError("Final step of path should have no rotation commands, pretty sure")
                        
                        #prep path input to recursive
                        path = valid_path[-1:]
                        expected_result = self.runPath(path, copy.deepcopy(valid_path_board), 0, 0)  #modify the path to terminus, for use in the recursive

                        #recursive
                        #what if we already win here? hopefully the recursive can detect that
                        # debug(f"Hitting recursive from play game: path={path}, board={valid_path_board}")
                        valid_paths_len_prior = len(self.valid_paths)
                        debug(f"Calling recursive: max depth={self.max_depth}, len seed={len(valid_path)}")
                        expected_result = self.pathingRecursive(path, 0, valid_path_board, minimal, 0) #extra depth = max(0, self.max_depth - len(valid_path)
                        if len(self.valid_paths) > valid_paths_len_prior:
                            debug(f"Valid paths after this recursive: seed path length={len(valid_path)}, added paths={len(self.valid_paths)-valid_paths_len_prior}, len of one={len(self.valid_paths[valid_paths_len_prior])}, result={expected_result}")
                            for debug_index, debug_path in enumerate(self.valid_paths):
                                debug(f"Valid path after recursive: pathid={debug_index}, final coords = {debug_path[-1]['x']} {debug_path[-1]['y']}, path={debug_path}")
                            #extend all newly created valid paths with the og
                            # debug(f"Starting appending: len self={len(self.valid_paths)}, valid_paths_len_prior={valid_paths_len_prior}")
                            for i in range(valid_paths_len_prior, len(self.valid_paths), 1):
                                # debug(f"Appending: i={i}, valid_path={valid_path}, self.valid_paths[i]={self.valid_paths[i]}")
                                self.valid_paths[i] = valid_path[:-1] + self.valid_paths[i]
                                # debug(f"Resulting: self.valid_paths[i]={self.valid_paths[i]}")
                            debug(f"Valid path count after append: count={len(self.valid_paths)}, len[0]={len(self.valid_paths[valid_paths_len_prior])}, result={expected_result}")
                        else:
                            debug(f"Added no valid paths")

                        if time.time() - turn_start_time > 0.75: break #end if we only have 0.25 seconds or less left to make a decision
                        # if time.time() - turn_start_time > 0.73:
                        #     debug(f"Seconds elapsed: {time.time() - turn_start_time}")
                        if expected_result == 1: break
                    # debug(f"Valid path count: count={len(self.valid_paths)}, len[0]={len(self.valid_paths[0])}, result={expected_result}")

                    if len(self.valid_paths[0]) > 25: break #max depth we will search
                    if time.time() - turn_start_time > 0.75: break #end if we only have 0.25 seconds or less left to make a decision
                    if expected_result == 1: break
                    debug(f"Going another depth chunk, seconds elapsed={time.time()-turn_start_time}")

                debug(f"Valid paths final: {self.valid_paths}")
                #check if they all have the same rotation command for this step, if not... do what?

                #pick the path with the fewest rotations
                if expected_result == 0:
                    #picking path with fewest rotations
                    if len(self.valid_paths) > 0: #this should always be true
                        self.current_plan = min(self.valid_paths, key=lambda path: sum(1 for step in path if step["rotation_command"] != []))
                elif expected_result == 1:
                    if len(self.valid_paths) > 0:
                        #pick path with fewest rotations
                        self.current_plan = min(self.valid_paths, key=lambda path: sum(1 for step in path if step["rotation_command"] != []))
                elif expected_result == -1:
                    #pick longest path (first time we've discovered death)
                    if len(self.valid_paths) > 0:
                        self.current_plan = max(self.valid_paths, key=lambda path: len(path))

                #do a path cleanup step where we shift all rotations up to as early as possible, in case we need the time later
                #first move up the indy rotations, then the rock ones, in case later rocks change plans (pls let us not have to make rocks collide with each other)
                # print(f"Compressing plan: plan={self.current_plan}", file=sys.stderr, flush=True)
                icompressed = 0
                #first the INDYs
                for step_index, step in enumerate(self.current_plan):
                    if step["rotation_command"] != []:
                        if step["rotation_command"][4] == "INDY":
                            if step_index > icompressed: #if there are opens behind us
                                self.current_plan[icompressed]["rotation_command"] = step["rotation_command"]
                                step["rotation_command"] = []
                        icompressed += 1 
                #now the rocks (and everything)
                for step_index, step in enumerate(self.current_plan):
                    if step["rotation_command"] != []:
                        if step_index > icompressed: #if there are opens behind us
                            self.current_plan[icompressed]["rotation_command"] = step["rotation_command"]
                            step["rotation_command"] = []
                        icompressed += 1           
            print(f"Compressed plan: plan={self.current_plan}", file=sys.stderr, flush=True)

            #region resultAndExecution
            # print(f"After calc", file=sys.stderr, flush=True)   
            #expected result print
            if expected_result == None:
                #must have been using plan, so use cellEntry
                mykey = (self.xi, self.yi, self.entryi)
                if mykey in self.cellEntryValues:
                    expected_result = self.cellEntryValues[mykey]
                else:
                    print("Aborting due to no expected result")
            if expected_result == 1:
                print(f"Expecting win", file=sys.stderr, flush=True)
            elif expected_result == -1:
                print(f"Awaiting inevitable death", file=sys.stderr, flush=True)
            elif expected_result == 0:
                print(f"No win yet, paths count = {len(self.valid_paths)}", file=sys.stderr, flush=True)
            else:
                print(f"Weird expected_result={expected_result}", file=sys.stderr, flush=True)
            #format and make decision
            if self.current_plan == []: raise RuntimeError("Aborting, no plan (not coded to dance with death yet)")
            rotation_command = self.current_plan[0]["rotation_command"]
            if rotation_command != []:
                rotation_decision = f"{rotation_command[0]} {rotation_command[1]} {rotation_command[2]}"
            else:
                rotation_decision = "WAIT"
            self.path[0]["rotation_command"] = rotation_command
            #do it   
            # One line containing on of three commands: 'X Y LEFT', 'X Y RIGHT' or 'WAIT'
            # print(f"Before move {rotation_decision}", file=sys.stderr, flush=True)
            print(rotation_decision) #actual interface with external game engine
            # print(f"After move {rotation_decision}", file=sys.stderr, flush=True)
            #changes affect game world
            if rotation_command != []:
                self.board[rotation_command[1]][rotation_command[0]] = self.convertRoom(self.board[rotation_command[1]][rotation_command[0]], rotation_command[2])
            for valid_path in self.valid_paths: #remove this current step from pathing foresight
                valid_path.pop(0)
            #no need to pop current plan, it is same reference as one of the valid paths
            #endregion

myIndyPlayer = IndyPlayer()
myIndyPlayer.playGame()