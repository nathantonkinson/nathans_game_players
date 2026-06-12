import sys
import math
import copy
import time
from collections import Counter

# To debug: print("Debug messages...", file=sys.stderr, flush=True)
# seems to tolerate 1 but not 2 seconds of delay, at all stages of nitialization and play
# It has limitations on how much you can debug print (then says ran out of time, I think, and does...)
# Can use try: except: to isolate print debug on runtime errors

#could add backwards from bottom (but doesn't work well for huge maze, unless allowed to do that with infinite time before call first position)
#could add self timer to not exceed the 1 second
#could add keep looking for paths until done looking or find exit (don't stop at mere depth)
#could save 0 (neutral result) paths and just build on them or something
#check minimal rotations first
#check each rock kill rotation if in our path or other rock paths
#it might be simpler to proactively kill rocks rather than keep track of rock history shennanigans, or else we have to do deepcopy
#we are ignoring a situation where new rock added to existing solved plan collides with another rock before that other rock collides with a third, letting the 3rd kill us



room_types = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
entry_types = ["TOP", "LEFT", "RIGHT"]

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

    def cleanUpPath(self, path, initial_board):
        #takes a path, takes starting conditions, and recalculates path of indy and rocks based on the rotation commands
            #new rock indexes that appear at later points are new information, but that shouldn't happen since we are typically doing this from current decision state
        #returns -1 for indy death
        #returns ?? for no changes
        #returns ?? for changes but not death
        pass

    #need to do pathfinding, depth first, recursive
    def pathsfindRecursive(self, board, path):
        #find next room, next rock rooms
        #then iterate over all rotations of current room, finding ones that allow indy to enter from entry
        
        #calculate step, building info needed for next path line 
        # if self.xi == 8 and self.yi == 1:
        #     print(f"Recursive top: prev={path[-1]}", file=sys.stderr, flush=True)
        prev = path[-1]
        # print(f"Path = {path}, Prev = {prev}", file=sys.stderr, flush=True)
        xchange, ychange, ientry = self.nextRoomOffset(prev["room_type"], prev["entry"])
        x = prev["x"]+xchange
        y = prev["y"]+ychange
        #learn from the past explorations. The play game function will delete memory if new rocks require recalculation
        mykey = (x, y, ientry)
        if mykey in self.cellEntryValues:
            if self.cellEntryValues[mykey] in [1, -1]: #fully explored results here
                return self.cellEntryValues[mykey]
        # print(f"{prev['x']}, {x}, {xchange}, {prev['y']}, {y}, {ychange}", file=sys.stderr, flush=True)
        current_room_type = self.board[y][x]
        #rock stuff
        rock_info_unmodified = []
        # print(f"Calculating rock movement: Path = {path}, Prev rock info = {prev['rock_info']}", file=sys.stderr, flush=True)
        for i, rock in enumerate(prev["rock_info"]):
            if rock != (None, None, None):
                #check motion through prior room
                xchange, ychange, rock_entry = self.nextRoomOffset(
                    board[rock[1]][rock[0]]
                    , rock[2])
                if not ((0 <= rock[0]+xchange <= self.w - 1) and (0 <= rock[1]+ychange <= self.h-1)): #rock went OOB
                    rock_info_unmodified.append((None, None, None)) #put nothing here so the individual rocks retain ther index
                else:
                        #check ok for condition of this next/current room
                        xtemp, _, _ = self.nextRoomOffset(
                            board[rock[1]+ychange][rock[0]+xchange]
                            , rock_entry
                        )
                        #rock didn't get destroyed or OOB
                        if xtemp is not None:
                            # print(f"Rock moving to: {[rock[0]+xchange, rock[1]+ychange, rock_entry]}", file=sys.stderr, flush=True)
                            rock_info_unmodified.append((rock[0]+xchange, rock[1]+ychange, rock_entry)) #rock could still be entering indys room, which we could rotate and kill it, in which case we will amend this
                        else:
                            rock_info_unmodified.append((None, None, None)) #put nothing here so the individual rocks retain ther index
            else:
                rock_info_unmodified.append((None, None, None))
        #rock dual-annihilation
        # print(f"Countering rock info: rock_info={rock_info}", file=sys.stderr, flush=True)
        counts = Counter(rock_info_unmodified)
        repeats = {rock for rock, c in counts.items() if c > 1}
        rock_info_unmodified = [(None, None, None) if rock in repeats else rock for rock in rock_info_unmodified]
        #will check problematic rocks for each rotations, could do here doesn't save much

        #iterate over all rotations
        current_room_type = self.board[y][x]
        room_types_covered = []
        best_result = -1
        for r in range(4):
            #not rotating here at top to try no rotation first

            #ignore duplicate rotations (like type 2 and 3)
            if current_room_type in room_types_covered:
                continue
            #can't rotate locked room. Indy can't path back on himself so no need to check for that
            if current_room_type < 0 and r != 0: 
                continue

            #initialization
            invalid = False
            add_rotations = []  #x, y, direction, maximum step
            if r == 0:
                pass
            if r == 1:
                add_rotations.append([x, y, "RIGHT", len(path)-1])
            if r == 2:
                add_rotations.append([x, y, "RIGHT", len(path)-1])
                add_rotations.append([x, y, "RIGHT", len(path)-1])
            if r == 3:
                add_rotations.append([x, y, "LEFT", len(path)-1])

            #check if this rotation doesn't kill us or do other weird things
            ixchange, iychange, exit_direction = self.nextRoomOffsets[(abs(current_room_type), ientry)]
            # print(f"{xchange}, {x}, {ychange}", file=sys.stderr, flush=True)
            if ixchange is None or x+ixchange < 0 or x+ixchange > self.w - 1 or y+iychange < 0 or y+iychange > self.h: #no -1 because allow for exit
                invalid = True #oob or can't enter at this rotation
            if invalid == False and y+iychange == self.h and x+ixchange != self.exit_x: #below bottom of map, wrong exit
                invalid = True
            
            #add rotations needed for rock problems (inside rotation loop in case the rotation already kills the rocks)
            prior_rock_information = [] #use this to restore after recursion
            rock_info_modified = copy.deepcopy(rock_info_unmodified) #rock indexes
            if invalid == False:
                for rock_index, rock in enumerate(rock_info_unmodified): #look through all rocks for having same x y as us
                    if rock[0] == x and rock[1] == y: #uh oh we got hit
                        xchange, ychange, _ = self.nextRoomOffsets[(abs(current_room_type), rock[2])]
                        if xchange is None: #rock died on entry, erase it
                            rock_info_modified[rock_index] = (None, None, None)
                        else: #rock survived current rotation of indys next room, so need to kill it earlier
                            #look backward up the rock path for a place where we can kill it
                            rock_dead = False
                            for step_index in range(len(path) - 2, -1, -1): #len(path)-2 because we collide at len-1, so change must be made at -2 or earlier.
                                #step_index = step prior to rock death, where rock is now
                                this_rock_info = path[step_index]["rock_info"]
                                if rock_index >= len(this_rock_info): #if we get past rocks origin, we're stuck
                                    invalid = True
                                    break  
                                #check if we can rotate next room to kill rock
                                kill_rock = path[step_index+1]["rock_info"][rock_index] #where the rock will be killed (the room it runs into)
                                kill_room = board[kill_rock[1]][kill_rock[0]]
                                if kill_room < 0: continue #can't rotate this room
                                #check if room has a rock in it at time of rotate (step_index)
                                if any(preventing_rock[0] == x and preventing_rock[1] == y for preventing_rock in path[step_index+1]["rock_info"]) == True: continue
                                #check if the room is in indys path
                                if any(step["x"] == kill_rock[0] and step["y"] == kill_rock[1] for step in path) == True: continue
                                #check if room is in path of different rock (2 for 1 I guess?)
                                if any(rock_index != else_rock_index and else_rock[0] == kill_rock[0] and else_rock[1] == kill_rock[1] for step in path for else_rock_index, else_rock in enumerate(step["rock_info"])) == True:
                                    print(f"Kill rock {kill_rock} action is going to affect another rock", file=sys.stderr, flush=True)
                                #attempt rotations to kill rock
                                for rock_rotation in range(1, 4, 1): #start at 1 because 0 let it live, stopping at 4 is exclusive
                                    kill_room = self.convertRoom(kill_room, "RIGHT")
                                    xchange, ychange, _ = self.nextRoomOffset(kill_room, kill_rock[2])
                                    if xchange is None:
                                        #yay we found a way to kill it
                                        if rock_rotation == 1:
                                            add_rotations.append([kill_rock[0], kill_rock[1], "RIGHT", step_index])
                                        if rock_rotation == 2:
                                            add_rotations.append([kill_rock[0], kill_rock[1], "RIGHT", step_index])
                                            add_rotations.append([kill_rock[0], kill_rock[1], "RIGHT", step_index])
                                        if rock_rotation == 3:
                                            add_rotations.append([kill_rock[0], kill_rock[1], "LEFT", step_index])
                                        rock_dead = True
                                        # print(f"Killed rock: index={rock_index}, via move (maybe 1/2)={add_rotations[-1]}", file=sys.stderr, flush=True)
                                        break
                                if rock_dead == True: 
                                    #need to erase the rock from rock history I guess
                                    for temp_step_index in range(step_index+1, len(path), 1):
                                        prior_rock_information.append((temp_step_index, rock_index, path[temp_step_index]["rock_info"][rock_index]))
                                        path[temp_step_index]["rock_info"][rock_index] = (None, None, None)
                                    rock_info_modified[rock_index] = (None, None, None) #hopefully no problems because we're iterating over this
                                    break
                            if rock_dead == False: #unable to find way to kill rock
                                invalid = True
                                break

            #done adding rotations, see if it can fit in our schedule
            prior_path_information = [] #just a list of path indexes we changed from [] to a rotation
            if invalid == False: 
                # append to path if possible
                # find latest in path we can do these rotations
                for ir, new_rotation in enumerate(add_rotations):
                    found_slot = False
                    max_index = len(path) - 1 if len(new_rotation) <= 3 else new_rotation[3]
                    for pi in range(max_index, -1, -1):
                        if len(new_rotation) >= 4:
                            if pi > new_rotation[3]: #this is too late in the path to make this change
                                break
                        if path[pi]["rotation_command"] not in [[], [None, None, None], None, [None, None, None, None]]: continue #not an available slot to put in a rotation command
                        if any(preventing_rock[0] == new_rotation[0] and preventing_rock[1] == new_rotation[1] for preventing_rock in path[pi]["rock_info"]) == True: continue
                        prior_path_information.append(pi)
                        path[pi]["rotation_command"] = new_rotation
                        found_slot = True
                        break
                    if found_slot == False:
                        invalid = True #not enough actions to rotate this enough
                        #undo prior rotations (only applies to r==2)
                        for i in range(ir-1, -1, -1): #stop at -1 and -1 increment
                            #find latest path point where this rotation was done
                            for step in path:
                                if step["rotation_command"] == add_rotations[i]:
                                    step["rotation_command"] = []
                                    break #found this rotation undo, move on to next undo rotation 
                        break #done undoing, leave the check for placing rotations in path
                #end of placing rotations in path
            
            #recursive
            # print(f"Future pathing point: x={x}, y={y}, type={current_room_type}, invalid={invalid}, depth={len(path)}", file=sys.stderr, flush=True)
            if invalid == False:

                # new_path = copy.deepcopy(path)
                # path.append([x, y, current_room_type, ientry, [], ])
                path.append({"x":x, "y":y, "room_type":current_room_type, "entry":ientry, "rotation_command":[], "rock_info":rock_info_modified})
            
                #call next or (if at end) record successful path
                # print(f"Future pathing point: x={x}, y={y}, type={current_room_type}, invalid={invalid}, depth={len(path)}", file=sys.stderr, flush=True)
                #reached end or max depth
                if len(path) == self.max_depth or (y+iychange == self.h and x+ixchange == self.exit_x): #exited properly
                    self.valid_paths.append(copy.deepcopy(path))
                    self.found_path = True
                    if y+iychange == self.h and x+ixchange == self.exit_x: #proper exit
                        best_result = 1
                    else:
                        best_result = max(best_result, 0)
                    # print(f"Added valid path = {path}", file=sys.stderr, flush=True)
                else: #not end or max depth, so keep going
                    #change the board
                    for rotation in add_rotations:
                        board[rotation[1]][rotation[0]] = self.convertRoom(board[rotation[1]][rotation[0]], rotation[2])
                    this_result = self.pathsfindRecursive(board, path)
                    best_result = max(best_result, this_result)
                
                #we have exited recursive part, pop off the added stuff
                path.pop()
                #board
                for rotation in add_rotations:
                    undo_dir = "RIGHT" if rotation[2] == "LEFT" else "RIGHT"
                    board[rotation[1]][rotation[0]] = self.convertRoom(board[rotation[1]][rotation[0]], undo_dir)
                #rotation commands
                for path_rotation in prior_path_information:
                    path[path_rotation]["rotation_command"] = []
                #rock history
                for rock_event in prior_rock_information:
                    path[rock_event[0]]["rock_info"][rock_event[1]] = rock_event[2]

            #if we need to be efficient, just use the first path we found and go up a level
            if self.found_path == True: 
                # print(f"Break due to found path", file=sys.stderr, flush=True)
                break
            #try next rotation
            room_types_covered.append(current_room_type)
            if current_room_type > 0:
                current_room_type = self.convertRoom(current_room_type, "RIGHT")
            else:
                break #this room can't be rotated, done searching rotations
            #loop to top to see if next rotation is useful
        
        # if best_result in [0, 1]:
        #     print(f"Writing to cellEntryValues: {mykey}={best_result}", file=sys.stderr, flush=True)
        self.cellEntryValues[mykey] = best_result
        return best_result

    def playGame(self):

        # game loop
        self.cellEntryValues = {} #key (x, y, entry), value=-1 (dead), 0 (limit), 1 (escape)
        while True:

            #get info and compare to plan (if plan exists)
            self.getCurrentInfo() #at top so we don't have to call it in init
            self.path.append({"x":self.xi, "y":self.yi, "room_type":self.board[self.yi][self.xi], "entry":self.entryi, "rotation_command":[None, None, None], "rock_info":self.rock_info})
            #if we had a plan, check if we're where we expected, and rocks as expected, and align rocks to prior if some died, and check for new rocks
            # print(f"Prior adjust: rock_info={self.rock_info}", file=sys.stderr, flush=True)
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
                    temp = copy.deepcopy(p["rock_info"])
                    temp.extend(new_rocks) #this returns None, not the list, otherwise we could do this on one line
                    self.rock_info = temp

                #check if new rocks require alteration to plan. Only need this if guaranteed win/lose since we delete memory of undetermined
                if new_rocks != [] and expected_result in [1, -1]:
                    # if self.xi == 5:
                    #     print(f"New rock no problems?: new_rocks={new_rocks}, plan[0]rockinfo={p['rock_info']}, self rock info={self.rock_info}", file=sys.stderr, flush=True)
                    for rock in new_rocks:
                        rx = rock[0]
                        ry = rock[1]
                        re = rock[2]
                        board = copy.deepcopy(self.board)
                        for step in self.current_plan: #we didn't already add rock to plan, so can start with current. But should pass all 1st step checks
                            #is rock dead in invalid room?
                            #calc next location of rock
                            xchange, ychange, re = self.nextRoomOffset(board[ry][rx], re)
                            #check if rock died from the room its in right now
                            if not (xchange is not None and (0 <= rock[0]+xchange <= self.w - 1) and (0 <= rock[1]+ychange <= self.h-1)): break 
                            #check rock collision with other rocks 
                            for r in step["rock_info"]:
                                if r[0] == rx and r[1] == ry: 
                                    calculation_required = True #just in case unlikely situation where this causes early collision that prevents later collision, that allows a rock to kill us.
                                    break
                            #check if rock in same space as indy (won't for first, or he's dead already)
                            if (rx == step["x"] and ry == step["y"]):
                                calculation_required = True
                                break
                            # print(f"{step}, {step['rotation_command']}", file=sys.stderr, flush=True)
                            #check if rock in a rotation command location
                            if step["rotation_command"] not in [None, [], [None, None, None], [None, None, None, None]]:
                                if (rx == step["rotation_command"][0] and ry == step["rotation_command"][1]):
                                    calculation_required = True
                                    break
                            #rock not gone (or now colliding), record it
                            step["rock_info"].append((rx, ry, re)) #write it into plan (I don't think we already do by default upon learning of it)
                            # print(f"Added rock to step: rock_info={step['rock_info']}", file=sys.stderr, flush=True)
                            # if rx == 1 and ry == 5:
                            #     print(f"Why is this still being written? xchange={xchange}, rx={rx}, ry={ry}, room type={board[ry][rx]}, entry={re}, step={step}", file=sys.stderr, flush=True)
                            #apply rotation command
                            if step["rotation_command"] not in [[], None, [None, None, None], [None, None, None, None]]:
                                board[step["rotation_command"][1]][step["rotation_command"][0]] = self.convertRoom(board[step["rotation_command"][1]][step["rotation_command"][0]], step["rotation_command"][2])
                            #rock still moving, update rock info
                            rx = rx+xchange
                            ry = ry+ychange
                            re = re
                            #rock still moving, go to next step
                        if calculation_required == True: break
                    if calculation_required == False:
                        print(f"New rocks don't interefere with plan", file=sys.stderr, flush=True)
                #if require recalculation, destroy current plan
                if calculation_required == True:
                    self.current_plan = []
                    self.cellEntryValues = {}
                #if result indeterminate, still need to do some calculation, but don't destroy memory
                if calculation_required == False and expected_result == 0:
                    calculation_required = True
            
            expected_result = None

            print(f"Recalc occurring?: recalc={calculation_required}", file=sys.stderr, flush=True)
            # print("I don't think we're getting calc required on expect=0 for underground complex??")
            if calculation_required == True:
                #find location we're going to from our current
                current_room_type = myIndyPlayer.board[self.yi][self.xi]
                #purge memory of entries that hit depth max without failure or egress
                self.cellEntryValues = {k: v for k, v in self.cellEntryValues.items() if v != 0}
                    #I can't guarantee the cellEntryValues time save is foolproof. It probably is due to can't go up or turn around.
                self.valid_paths = [] #could probably find a way to keep this around, and just build on the end of these
                    #we are at least keeping self.current_plan around
                self.found_path = False
                self.max_depth = 20
                # print(f"Calling find path: rock info={self.rock_info}", file=sys.stderr, flush=True)
                #x, y, room type, entry, rotation command [x, y, direction], rock_info [[x, y, entry]]
                path = [{"x":self.xi, "y":self.yi, "room_type":current_room_type, "entry":self.entryi, "rotation_command":[None, None, None], "rock_info":self.rock_info}]
                # print(f"Player call recursive: Path={path}", file=sys.stderr, flush=True)
                expected_result = self.pathsfindRecursive(copy.deepcopy(self.board), path)

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
                icompressed = 0
                # print(f"Compressing plan: plan={self.current_plan}", file=sys.stderr, flush=True)
                for step_index, step in enumerate(self.current_plan):
                    if step["rotation_command"] not in [[], None, [None, None, None], [None, None, None, None]]:
                        if step_index > icompressed:
                            self.current_plan[icompressed]["rotation_command"] = step["rotation_command"]
                            step["rotation_command"] = []
                        icompressed += 1            
            print(f"Compressed plan: plan={self.current_plan}", file=sys.stderr, flush=True)

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
                print(f"weird expected_result={expected_result}", file=sys.stderr, flush=True)
            #format and make decision
            if self.current_plan == []: raise RuntimeError("Aborting, no plan (not coded to dance with death yet)")
            rotation_command = self.current_plan[0]["rotation_command"]
            if rotation_command not in [[], None, [None, None, None]]:
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
            if rotation_command not in [[], None, [None, None, None]]:
                self.board[rotation_command[1]][rotation_command[0]] = self.convertRoom(self.board[rotation_command[1]][rotation_command[0]], rotation_command[2])
            self.current_plan.pop(0) #remove decision we made from the plan

myIndyPlayer = IndyPlayer()
myIndyPlayer.playGame()


