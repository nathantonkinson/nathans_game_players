#region plan and todo

#QOL IDEAS
#We could add saving replays to the GameMatch

#QUESTIONS
#I still don't understand why an untrained net does just as well as a piece valuation in MCTS, but whatever. I mean, once it gets close to end of game it will help. Could try to check that.

#IDEAS - reversi
#replay buffer - store self-play so we can train models on it without doing the time-intensive searching again
#   if we replay stuff over and over it might prevent brittle/erratic training too, best practice. Replay buffer can be much larger than #games played each cycle
#different math methods for value and policy (kl, mse, else)
#make sure the outputs of network, policy target, and value target are normalized (>=0 and sum to 1)
#modify policy outputs with temperature (raise all outputs nodes to power of 1/T) to artificially encourage exploration early on (if T>1). This is applied to AFTER the MCTS search to the final decision made for each move in self-play
#policy_target = ?
#   actual move made using best methods we have (current), 1 and 0s
#   1=best move we think using mcts, 0=invalid moves, 0.1 for valid moves or some other thing that takes into account valid moves?
#   ***mcts scores for each depth=1 move, possibly normalized to sum to 1. alpha zero does this
#policy pred
#   neural result of input
#   net output and zero out invalid moves, possibly normalize so valid moves sum to 1
#valuation/rollout
#   pieces - designed heuristic
#   heuristic - a more complex designed heuristic, extra weight to corners and edges or 2 away from corners and edges
#   random - moves until game done
#   value_head - just one run of the net to get value head result
#   policy_play - pure policy play until game done (just like our testing at end vs random)
#use convolutional layers in the net
#make a separate net for the last few moves, and train from random positions (or random games) that are near the end, the back it up and use the good net for valuation or whatever 
#whether or not to use policy priors in MCTS

#GENERIC GAME
#cartpole etc had env.step with reward...
#   self-defines its observation space and action space, similar to i/os of a network


#endregion

#region imports and autoconfig
import os
import sys
import copy
import math
import random
import time
import uuid

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

import tkinter as tk
from tkinter import simpledialog, messagebox

from collections import defaultdict

#ml stuff
import torch
import torch.nn as nn
import torch.nn.functional as F

os.chdir(os.path.dirname(os.path.abspath(__file__))) #so filenames without paths point to local directory
plt.ion()  # Turn on interactive mode, idk exactly what this is but trying to update display and not make new one each time
# print("Running:", os.path.abspath(__file__))
# print(__name__) #is "__main__" if this is the primary file run, while all others in sys.modules[] have their import names

#CAN TELL USER TO DO THIS, or put this in a setup.bat file which can be run from console or double-clicked maybe
# python -m venv venv #virtual environment to run everything, so they don't mess up their local install stuff
# venv\Scripts\activate
# pip install -r requirements.txt

#endregion

#region config
BOARD_SIZE = 8
n_observations = BOARD_SIZE ** 2 #could just embed these in the net code but whatever
n_actions = BOARD_SIZE ** 2
#endregion

#region game and interface
class ReversiGame: #reset, get_game_state, check_move_validity, valid_moves, has_valid_moves, make_move
    def __init__(self, board_size=BOARD_SIZE):
        if board_size % 2 != 0 or board_size < 4:
            raise ValueError("Board size must be even and at least 4")
        self.board_size = board_size
        #self.board, winner, and current_player are created in the reset
        self.reset()

    def reset(self):
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        mid = self.board_size // 2 #due to index at 0, this is the bottom right of the 4 center squares
        #populate 4 center squares with starting pieces
        self.board[mid-1][mid-1] = 1  # Player 1
        self.board[mid-1][mid] = -1   # Opponent
        self.board[mid][mid-1] = -1
        self.board[mid][mid] = 1
        self.current_player = 1  # 1 or -1
        #to cut things down by 4, I'm actually going to make the first move, which is symmetric and doesn't really matter
        self.board[mid-2][mid] = 1
        self.board[mid-1][mid] = 1 #flipped piece
        self.current_player = -1
        #no winner yet
        self.winner = None  # None, 1, -1, 0 for tie

    def get_game_state(self):
        return {
            # 'board': [row[:] for row in self.board], #can't return the board directly since it's mutable, so we return a copy
            'board': copy.deepcopy(self.board),
            'current_player': self.current_player,
            'winner': self.winner
        }

    def check_move_validity(self, row, col, player = None): #returns true or false. Doesn't collect flips, doesn't check whose turn it is or if game is over
        if player is None: player = self.current_player

        if self.board[row][col] != 0: #can't play on an occupied cell
            return False
        
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            found_opponent = False
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] == 0:
                    break
                if self.board[r][c] == player:
                    if found_opponent:
                        return True
                    break
                else:
                    found_opponent = True
                r += dr
                c += dc
        return False
    
    def valid_moves(self, player = None): #returns list of (r,c) tuples
        if player is None: player = self.current_player
        moves = []
        if self.winner is not None: return moves
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.check_move_validity(r, c, player):
                    moves.append((r, c))
        return moves
    def has_valid_moves(self, player = None): #just checks any, and doesn't store list
        if player is None: player = self.current_player
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self.check_move_validity(r, c, player):
                    return True
        return False

    def make_move(self, row, col): #includes pass turn and end of game win/loss action
        #check if move is valid
        if self.winner is not None: #can't make move if game is already over
            return None
        if not (0 <= row < self.board_size and 0 <= col < self.board_size): #move is out of bounds
            return None
        if self.board[row][col] != 0: #move is not on an empty cell
            return None
        
        #check if move is valid (results in flipping opponent pieces)
            #not using check_move_validity here since we also need to collect flips
        #and collect pieces to flip
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        valid = False
        flips = []
        for dr, dc in directions:
            r, c = row + dr, col + dc
            temp_flips = []
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board[r][c] == 0:
                    break
                if self.board[r][c] == self.current_player:
                    if temp_flips: #only valid if we found opponent pieces to flip
                        flips.extend(temp_flips)
                        valid = True
                    break
                else:
                    temp_flips.append((r, c))
                r += dr
                c += dc
        if not valid:
            return None

        #move does not flip any opponent pieces, so it's invalid
        if flips is None: 
            return None
        
        #actually make the move and flip pieces
        # print("")
        # print("Board before move:")
        # for display_row in self.board:
        #     print(display_row)
        # print("Move", (row, col))
        self.board[row][col] = self.current_player
        for fr, fc in flips:
            self.board[fr][fc] = self.current_player
        
        #stuff about passing turn
        if self.has_valid_moves(-self.current_player): #if opponent has valid moves, switch player
            self.current_player = -self.current_player
        else: #if we also do not have valid moves, game is over
            if not self.has_valid_moves(self.current_player):
                p1_count = sum(row.count(1) for row in self.board)
                p2_count = sum(row.count(-1) for row in self.board)
                if p1_count > p2_count:
                    self.winner = 1
                elif p2_count > p1_count:
                    self.winner = -1
                else:
                    self.winner = 0
        return #self.get_game_state()

    def determine_winner(self): #only call this if you're sure the game is over
        #could put a check in here to make sure game is actually over, but it could slow us down
        p1_count = sum(row.count(1) for row in self.board)
        p2_count = sum(row.count(-1) for row in self.board)
        if p1_count > p2_count:
            self.winner = 1
        elif p2_count > p1_count:
            self.winner = -1
        else:
            self.winner = 0
        return self.winner

class GameMatch: #pits agents against each other for n games and does the display interface work
    def __init__(self, agentA, agentB, board_size=BOARD_SIZE, display=False, printProgress=False):
        #accepts classes with a function "player(game)" that output a move and an optional valuation of the position 
        self.agentA = agentA
        self.agentB = agentB
        self.board_size = board_size
        self.game = ReversiGame(self.board_size) #will reset this between each game
        self.results = defaultdict(int) #win/loss/tie counts
        self.computeTime = [0, 0]
        self.display = display
        self.printProgress = printProgress
        self.agents = [self.agentA, self.agentB]
        if self.display == True:
            self.display_create()
    
    def play_game(self):
        #play single game
        self.game.reset()
        random.shuffle(self.agents) #randomize who goes first
        self.valuation_black = 0 #I know they have real valuations from initial state but I'm lazy. I'll fix this later
        self.valuation_white = 0
        self.display_afterMove()
        move_count = 0
        
        while self.game.winner is None:
            game_copy = copy.deepcopy(self.game)
            
            self.display_midMove()
            startTime = time.time()
            if self.game.current_player == 1:
                move, self.valuation_white = self.agents[0].player(game_copy)
                self.computeTime[0] += time.time() - startTime
            else:
                move, self.valuation_black = self.agents[1].player(game_copy)
                self.computeTime[1] += time.time() - startTime
            self.game.make_move(*move)
            move_count += 1
            # print(move_count)

            #might want to add a win check here or something so the display shows the win
            self.display_afterMove() #waits for key press to continue after display

        #return the winning agent, or None if tie
        if self.game.winner == 1:
            return self.agents[0]
        elif self.game.winner == -1:
            return self.agents[1]
        else:
            return None
    
    def play_n_games(self, game_count=1):
        #play n games and return win rates for each player and ties
        self.results = defaultdict(int) 
        for game_num in range(game_count):
            self.results[self.play_game()] += 1
            if self.printProgress: print(f"Match progress:{((game_num+1)/game_count)*100:.2f}%", end="\r", flush=True)
        return self.results

    def display_results(self):
        for agent in self.results:
            if agent is None:
                print("Ties:", self.results[agent])
            else:
                print(f"{agent.name} wins:", self.results[agent])
        print("Agent", self.agents[0].name, "took compute =", self.computeTime[0], "seconds")
        print("Agent", self.agents[1].name, "took compute =", self.computeTime[1], "seconds")

    def pause_popup(self):
        root = tk.Tk()
        root.withdraw()  # hide the empty main window
        messagebox.showinfo("Paused", "Press OK to continue...")
        root.destroy()
    def wait_for_key(self):
        key_pressed = {"done": False}

        def on_key(event):
            key_pressed["done"] = True

        cid = self.fig.canvas.mpl_connect("key_press_event", on_key)

        # Block until a key is pressed
        while not key_pressed["done"]:
            plt.pause(0.01)

        self.fig.canvas.mpl_disconnect(cid)

    def display_create(self):
        if self.display == False: return

        self.fig, self.ax = plt.subplots(1, 1, figsize=(10, 8))

        #config
        bar_width = 0.25
        gap_from_board = 0.25
        #hardcoded stuff includes green, white, black, circles at 0.4 radius, and font size 12 bold for player labels.

        # Draw board
        board_size = self.game.board_size
        # Green background
        self.ax.add_patch(patches.Rectangle((0, 0), board_size, board_size, facecolor='green', edgecolor='black', linewidth=2))
        # Draw grid lines
        for i in range(board_size + 1):
            self.ax.plot([i, i], [0, board_size], 'k-', linewidth=1)
            self.ax.plot([0, board_size], [i, i], 'k-', linewidth=1)

        # Make list of lists like board, but containing patches. All green and invisible at start
        self.board_patches = [[None for _ in range(board_size)] for _ in range(board_size)]
        for r in range(board_size):
            for c in range(board_size):
                self.board_patches[r][c] = patches.Circle((c + 0.5, board_size - r - 0.5), 0.4, facecolor='blue', edgecolor='black', linewidth=1)
                self.ax.add_patch(self.board_patches[r][c])
                self.board_patches[r][c].set_visible(False)
        
        #PLAYER Labels
        self.title_black =self.ax.text(board_size / 2, board_size + gap_from_board, "no player assigned yet" + " (Black 1st 1)", 
                ha='center', va='bottom', fontsize=12, fontweight='bold')
        self.title_white = self.ax.text(board_size / 2, -gap_from_board, "no player assigned yet" + " (White 2nd -1)", 
                ha='center', va='top', fontsize=12, fontweight='bold')
        #eval bars box and internal value (horizontal above/below titles), default at value=0=halfway
        self.ax.add_patch(patches.Rectangle((0, -gap_from_board - 1), board_size, bar_width, 
            facecolor='white', edgecolor='black', linewidth=1))
        self.eval_black = self.ax.add_patch(patches.Rectangle((0, -gap_from_board - 1), 0.5*board_size, bar_width, 
            facecolor='black', edgecolor='black', linewidth=1))
        self.ax.add_patch(patches.Rectangle((0, board_size + gap_from_board + 1), board_size, bar_width,
            facecolor='white', edgecolor='black', linewidth=1))
        self.eval_white = self.ax.add_patch(patches.Rectangle((0, board_size + gap_from_board +1), 0.5*board_size, bar_width,
            facecolor='black', edgecolor='black', linewidth=1))
        
        #display
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def display_afterMove(self):
        """Display the board with evaluation bars using matplotlib."""
        if self.display == False: return

        #players. Could put this in separate game start rendering, but meh
        if self.game.current_player == 1:
            self.title_black.set_text(self.agents[0].name + " (Black 1st 1) (ready to play on keypress)")
            self.title_white.set_text(self.agents[1].name + " (White 2nd -1) (waiting on opponent)")
        else:
            self.title_black.set_text(self.agents[0].name + " (Black 1st 1) (waiting on opponent)")
            self.title_white.set_text(self.agents[1].name + " (White 2nd -1) (ready to play on keypress)")

        # Update and add pieces as needed
        for r in range(self.game.board_size):
            for c in range(self.game.board_size):
                if self.game.board[r][c] == 0:
                    self.board_patches[r][c].set_visible(False)
                    continue
                if self.game.board[r][c] == 1: facecolor_use = 'black' 
                else: facecolor_use = 'white'
                self.board_patches[r][c].set_facecolor(facecolor_use)
                self.board_patches[r][c].set_visible(True)

        #EVAL BARS
        #if no eval provided, default to 50/50 = 0
        eval_p1 = self.valuation_black if self.valuation_black is not None else 0
        eval_p2 = self.valuation_white if self.valuation_white is not None else 0
        # Player 1 eval bar (left side)
        self.eval_black.set_width((eval_p1 + 1) / 2 * self.game.board_size)
        self.eval_white.set_width((eval_p2 + 1) / 2 * self.game.board_size)

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.1)  # Pause to update the display, could maybe do even faster

        # self.pause_popup()
        self.wait_for_key()
    def display_midMove(self):
        if self.display == False: return

        #players. Could put this in separate game start rendering, but meh
        if self.game.current_player == 1:
            self.title_black.set_text(self.agents[0].name + " (Black 1st 1) (thinking...)")
        else:
            self.title_white.set_text(self.agents[1].name + " (White 2nd -1) (thinking...)")

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.1)  # Pause to update the display, could maybe do even faster
#endregion

#region valuation function(s)
#these functions take in a board state and return a probability of winning 0-1
#should we allow for random and policy evaluations? I guess
def valuation(game, method, net=None):
    #returns 0 to 1, relative to current player
    simulated_game = copy.deepcopy(game)
    if net is not None: netAgent = NeuralNetAgent(net)

    if game.winner is not None: return game.winner*game.current_player
    match method:
        case "pieces":
            #proportion of pieces that are mine
            my_piece_count = sum(row.count(game.current_player) for row in game.board)
            opponent_piece_count = sum(row.count(-game.current_player) for row in game.board)
            valuation = my_piece_count / (my_piece_count + opponent_piece_count)
        case "value_head":
            if net is None: raise(NotImplementedError)
            #estimate win/loss using value head. Value should be between 0 and 1. 
            board_tensor = torch.tensor(
                [piece if piece == 0 else (1 if piece == game.current_player else -1) 
                    for row in game.board for piece in row],
                dtype=torch.float32
            ).unsqueeze(0)
            with torch.no_grad():
                net_output = net(board_tensor)
            value_head = net_output[0, 0].item()
            # policy_output = net_output[0, 1:]
            valuation = value_head
        case "policy_play":
            if net is None: raise(NotImplementedError)
            while simulated_game.winner is None:
                move = netAgent.player(simulated_game)[0]
                simulated_game.make_move(*move)
            valuation = 1 if simulated_game.winner == game.current_player else 0
        case "random":
            while simulated_game.winner is None:
                moves = simulated_game.valid_moves()
                move = random.choice(moves)
                simulated_game.make_move(*move)
            valuation = 1 if simulated_game.winner == game.current_player else 0
        case "heuristic":
            #This returns between -1 and 1
            
            #mobility (qty available moves) HIGH
            #corners HIGH
            #stability (locked pieces)
            #parity (try to force opponent to play in regions with even number of empty squares)
            #frontier discs (avoid my disks on edges, basically restrict their moves)
            #pieces (raw number of pieces)
            e = 0.001

            #mobility
            my_move_count = len(game.valid_moves())
            opponent_move_count = len(game.valid_moves(player=-game.current_player))
            m = (my_move_count - opponent_move_count)/(my_move_count + opponent_move_count + e)

            #corners
            corners = [game.board[0][0],game.board[BOARD_SIZE-1][0],game.board[0][BOARD_SIZE-1],game.board[BOARD_SIZE-1][BOARD_SIZE-1]]
            c = game.current_player*sum(corners)/(sum(1 for corner in corners if corner != 0)+e)

            #locked pieces
            my_locked_pieces = 0
            opponent_locked_pieces = 0
            axis = [(1,0), (1,1), (0,1),(-1,1)] #only 1/2 of the 4 axis
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if game.board[row][col] == 0: break
                    #check that in all 4 axis either: one of the two directions is all my pieces OR both directions are full
                    safe_axes = 0
                    for ar, ac in axis:
                        found_empty = False
                        for d in (1, -1):
                            found_opposite = False
                            r, c = row + ar*d, col + ac*d
                            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                                if game.board[r][c] == 0:
                                    found_empty = True
                                    break
                                if game.board[r][c] == -game.board[r][c]:
                                    found_opposite = True
                                r += ar*d
                                c += ac*d
                            if found_opposite == False and found_empty == False: 
                                #safe axes with +1 just below, don't do it twice lol
                                break
                        if found_empty == False:
                            safe_axes += 1
                    if safe_axes == 4:
                        if game.board[row][col] == game.current_player:
                            my_locked_pieces += 1
                        else:
                            opponent_locked_pieces += 1
            l = (my_locked_pieces - opponent_locked_pieces)/(my_locked_pieces + opponent_locked_pieces + e)

            #to-do - add parity on regions (how on earth do we determine this? This is like connect-4. Whoever goes first there is not determined

            #f = frontier disks
            directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
            frontier_disks = []
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if game.board[row][col] == 0: break
                    for dr, dc in directions:
                        if 0 <= row + dr < BOARD_SIZE and 0 <= col + dc < BOARD_SIZE:
                            if game.board[row+dr][col+dc] == 0:
                                frontier_disks.append(game.board[row][col])
                                break
            f = -game.current_player*sum(frontier_disks)/(len(frontier_disks)+e)

            #p = pieces
            p = sum(piece for row in game.board for piece in row)/(sum(1 for row in game.board for piece in row if piece != 0) + e)

            #t = percent game is finished
            early = sum(1 for row in game.board for piece in row if piece != 0)/(BOARD_SIZE**2) 
            late = 1-early
            # the early and lates should add to 1
            valuation = m*(early*0.40+late*0.15) + c*(early*0.30+late*0.25) + l*(early*0.15+late*0.20) + f*(early*0.15+late*0.10) + p*(early*0.00+late*0.30)
            
            return (valuation+1)/2 #switch from -1-1 to 0-1
        case _:
            raise(NotImplementedError)
    
    #separate line down here in case we want to switch between -1-1 vs 0-1 (current)
    return valuation 
#endregion

#region complete/finished players
#they init with game instance, and output (move, optional valuation, optional [move, valuation], optional depth_avg)

class randomPlayer:
    def __init__(self):
        self.name = "Random Player"
    def player(self, game):
        moves = game.valid_moves()
        if not moves:
            return None, None
        move = random.choice(moves)
        return move, None

class fullSolve:
    #15308 states
    def __init__(self, game=ReversiGame()):  
        self.name = "Full Solve Player"
        self.game = game
        if self.game.board_size > 4:
            raise Exception("Full solve only works for board size 4. Larger boards have way too many states to solve in a reasonable time")
        self.stateAdvice = dict() #key = board state and current player, value = current eval, and best move for current player
        self.filename_default = f'fullSolve_{BOARD_SIZE}.pt'

    def fullSolve_recursive(self, game=None):
        if game is None: game = self.game
        best_move = None
        best_value = -game.current_player #initialize best value as other player winning, can only get better
        for move in game.valid_moves():
            next_state = copy.deepcopy(game)
            next_state.make_move(*move)
            if next_state.winner is not None:
                move_value = next_state.winner
            else:
                move_value = self.fullSolve_recursive(next_state)
            if game.current_player == 1:
                if move_value >= best_value:
                    best_value = move_value
                    best_move = move
            else:
                if move_value <= best_value: #need to use <= to write not None moves when we are on a fully losing line
                    best_value = move_value
                    best_move = move
        self.stateAdvice[self.game_to_key(game)] = (best_move, best_value)
        return best_value
    def solveToMemory(self):
        self.fullSolve_recursive()
        self.save_results() #save to file after solving, so we don't lose it if we want to do something with it after

    def game_to_key(self, game):
        #"""Convert board and current player to a hashable key."""
        board_tuple = tuple(tuple(row) for row in game.board)
        return (board_tuple, game.current_player)
    def save_results(self, results_dict=None, filename=None):
        #"""Save minimax results to file."""
        if filename is None: filename = self.filename_default
        if results_dict is None: results_dict = self.stateAdvice
        torch.save(results_dict, filename)
        print(f"Saved {len(results_dict)} entries to {filename}")
    def load_results(self, filename=None):
        #"""Load minimax results from file."""
        if filename is None: filename = self.filename_default
        return torch.load(filename, weights_only=True) #weights avoids a security issue. I don't think this restricts us in any way

    def player(self, game, filename=None):
        
        if filename is None: filename = self.filename_default
        #retrieve or generate solution if not already in memory
        if not self.stateAdvice:
            if os.path.exists(filename):
                self.stateAdvice = self.load_results(filename)
            else:
                self.solveToMemory(game)
        
        #play the game
        return self.stateAdvice[self.game_to_key(game)] #returns move, eval

class HumanPlayer:
    def __init__(self):
        self.name = input("Enter your name: ")
        self.name = simpledialog.askstring(
            "Your Move",
            f"Enter your name."
        )
        
    def player(self, game):
        valid_moves = game.valid_moves()

        while True:
            # Create a temporary root for dialogs
            root = tk.Tk()
            root.withdraw()

            # Ask for input
            user_input = simpledialog.askstring(
                "Your Move",
                f"Enter move as row,col\nValid moves: {valid_moves}"
            )

            root.destroy()

            # User closed the window
            if user_input is None:
                # messagebox.showerror("Error", "You must enter a move.")
                continue

            # Try to parse input
            try:
                # Remove spaces, split by comma
                parts = user_input.replace(" ", "").split(",")
                if len(parts) != 2:
                    raise ValueError

                row = int(parts[0])
                col = int(parts[1])
                move = (row, col)

            except Exception:
                # messagebox.showerror("Error", "Invalid format. Use row,col")
                continue

            # Check if move is valid
            if move not in valid_moves:
                # messagebox.showerror("Error", f"{move} is not a valid move.")
                continue

            # Success (didn't hit any continue statements)
            return move, None

class minimax:
    def __init__(self, max_depth=5, valuation_method="heuristic", net=None):
        self.name = "Minimax: depth=" + str(max_depth) + ", val=basic piece"
        self.max_depth = max_depth
        self.net = net
        self.valuation_method = valuation_method

    def player(self, game, depth=0, alpha=float('-inf'), beta=float('inf')): #returns best move and best guaranteeable value for current player (lower values better for player=-1)
        #we could make an outer function player wrapper on this, but the recursive works fine as the player, so we'll keep it this way
        
        #alpha beta minimax search through reversi, is recursive
        #minimax saves compute by, once we've found forcing lines, ignoring other choices
            #more generally, ignoring moves that allow opponent to force a score worse for us than other moves we've already seen
        #game is a ReversiGame object
        #for board size = 4, for depth it takes seconds: d5=0.004s, d7=0.007s, d10=0.01s, d13=0.01s
        #   full solve is 15,000. This only requires 159
        #for board size = 6, for depth 14 it took 440sec
        #for board size = 8, for depth it takes seconds: d5=0.03s, d7=0.3s, d8=1s, d9=3.6s, d10=9.8s. Basically up by a factor of 3 each depth.

        if depth == 0: 
            self.calls = 0
        else:
            self.calls += 1

        #early easy checks on who won
        if game.winner is not None:
            return None, game.winner
        if depth == self.max_depth:
            return None, valuation(game, method=self.valuation_method, net=self.net)
        
        valid_moves = game.valid_moves()
        
        best_move = None
        if game.current_player == 1: #player 1, maximizer
            best_val = float('-inf')
            for move in valid_moves:
                next_state = copy.deepcopy(game)
                next_state.make_move(*move)
                _, eval = self.player(next_state, depth + 1, alpha, beta)
                if eval > best_val:
                    best_move = move
                    best_val = eval
                alpha = max(alpha, eval)
                if beta <= alpha or alpha == 1:
                    break
            # if depth == 0:
            #     if self.calls > 50:
            #         debug=1 
            #     print("Minimax: max_depth=" + str(self.max_depth) + ", resulted in function calls=" + str(self.calls))
            return best_move, alpha
        else: #player 2/-1cx cx 4
            best_val = float('inf')
            for move in valid_moves:
                next_state = copy.deepcopy(game)
                next_state.make_move(*move)
                _, eval = self.player(next_state, depth + 1, alpha, beta)
                if eval < best_val:
                    best_val = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha or beta == -1:
                    break
            # if depth == 0: 
            #     if self.calls > 50:
            #         debug=1
            #     print("Minimax: max_depth=" + str(self.max_depth) + ", resulted in function calls=" + str(self.calls))
            return move, beta

    # def valuation_piece(self, game): #returns probability of win of player 1. For the moment will be manual, might make a neural net later to estimate this
    #     if game.winner is not None:
    #         return game.winner
    #     else:
    #         #returns a number between -1 and 1 based on piece count
    #         p1_count = sum(row.count(1) for row in game.board)
    #         p2_count = sum(row.count(-1) for row in game.board)
    #         return (p1_count - p2_count) / (p1_count + p2_count)

class MCTSWithPUCT:
    """Monte Carlo Tree Search with optional PUCT (netural net guidance).
    This is exactly (so says copilot) what alpha zero uses in actual execution"""
    
    def __init__(self, net=None, iterations=1000, rollout_mode="value_head"):
        #could do something where we get filename of net?? not yet that fancy
        net_text = "yes" if net is not None else "no"
        self.name = "MCTS-PUCT: net=" + net_text + ", iterations=" + str(iterations) + ", value=" + rollout_mode
        self.net = net
        self.iterations = iterations
        self.rollout_mode = rollout_mode #pieces (for proportion of pieces) or random (make random moves until game end)
        self.agent = NeuralNetAgent(self.net)

    class MCTSNode:
        def __init__(self, parent_class_instance, game_state, parent=None, move=None):
            self.game_state = game_state
            self.valid_moves = game_state.valid_moves()
            self.parent = parent
            self.move = move
            self.children = []
            self.visits = 0
            self.wins = 0 #is actually a sum of valuation, where value is 0 to 1
            #inheritance stuff
            self.parent_class = parent_class_instance
            self.net = self.parent_class.net
            self.root_state = self.parent_class.root_state
            self.root_player = self.root_state.current_player
            
            # Get prior probabilities from network
            if self.net is not None and len(self.valid_moves) > 0:
                self.priors = self._get_priors()

        def _get_priors(self):
            """Get policy priors from neural network."""
            board_tensor = torch.tensor(
                [piece if piece == 0 else (1 if piece == self.game_state.current_player else -1)
                    for row in self.game_state.board for piece in row],
                dtype=torch.float32
            ).unsqueeze(0)
            
            with torch.no_grad():
                net_output = self.net(board_tensor)
            policy_output = net_output[0, 1:]
            
            # Create prior dict for valid moves
            priors = {}
            for move in self.valid_moves:
                move_idx = move[0] * len(self.game_state.board) + move[1]
                priors[move] = policy_output[move_idx].item()
            
            # Normalize priors (nonnegative and sum to 1)
            total = sum(priors.values())
            if total > 0:
                priors = {m: p / total for m, p in priors.items()}
            else:
                uniform = 1.0 / len(self.valid_moves)
                priors = {m: uniform for m in self.valid_moves}
            
            return priors

        def is_fully_expanded(self):
            #will return true if game has ended (valid moves will be an empty list)
            return len(self.children) == len(self.valid_moves)

        def best_child(self, c_param=1.4):
            #copilot says c_param =4 for training, but between 1 and 2 for execution
            if self.net is not None: c_param = 1
            choices_weights = []
            for child in self.children:
                exploitation = child.wins / child.visits
                priors_factor = 1 if self.net is None else self.priors[child.move] 
                exploration = c_param * priors_factor * math.sqrt(self.visits) / (1 + child.visits)
                puct_score = exploitation + exploration
                choices_weights.append(puct_score)
            return self.children[choices_weights.index(max(choices_weights))]

        def expand(self):
            tried_moves = [child.move for child in self.children]
            for move in self.valid_moves:
                if move not in tried_moves:
                    next_state = copy.deepcopy(self.game_state)
                    next_state.make_move(*move)
                    child_node = MCTSWithPUCT.MCTSNode(self.parent_class, next_state, parent=self, move=move)
                    self.children.append(child_node)
                    return child_node
            return None

        def rollout(self):
            #returns value between 0 to 1 estimating probability of win
            #with no net, we use a valuation function (pieces by default), there's also an option for random play until game end
            if self.game_state.winner is not None:
                if self.game_state.winner == self.root_player:
                    return 1
                else:
                    return 0

            current_value = valuation(self.game_state, method=self.parent_class.rollout_mode, net=self.net)
            if self.game_state.current_player == self.root_player: 
                value = current_value
            else:
                value = 1 - current_value 

            return value

        def backpropagate(self, result):
            self.visits += 1
            self.wins += result #result is 0 to 1 probability of win
            if self.parent:
                self.parent.backpropagate(result)

    def player(self, root_state):
        self.root_state = root_state
        root_node = self.MCTSNode(self, root_state)
        depth_sum = 0
        depth_hits = defaultdict(int) #number of rollouts at each depth

        for _ in range(self.iterations):
            node = root_node
            current_depth = 0

            # Selection
            while node.is_fully_expanded() and node.children:
                node = node.best_child()
                current_depth += 1

            # Expansion
            if not node.is_fully_expanded():
                node = node.expand()
                current_depth += 1

            # Simulation
            result = node.rollout()
            depth_sum += depth_sum
            depth_hits[current_depth] += 1

            # Backpropagation
            node.backpropagate(result)

        best_child = root_node.best_child(c_param=0)
        valuation = root_state.current_player * (best_child.wins - (best_child.visits - best_child.wins)) / best_child.visits #change valuation into -1 to 1 (absolute)
        choices = [] #(move, weight)
        for child in root_node.children:
            exploitation = child.wins / child.visits
            # priors_factor = 1 if self.net is None else self.priors[child.move] 
            # exploration = c_param * priors_factor * math.sqrt(self.visits) / (1 + child.visits)
            puct_score = exploitation #+ exploration
            # choices.append((child.move, child.visits))
            choices.append((child.move, puct_score))
        
        # print(depth_hits)

        return best_child.move, valuation, choices, depth_sum/self.iterations

class NeuralNetAgent:
    #actual AlphaZero still uses MCTS during actual play. But this one should be lightning fast.
    def __init__(self, net=None, filename=None):
        self.name = "Neural Net Agent"
        if net is not None:
            self.net = net
        elif filename is not None:
            self.net = torch.load(filename, weights_only=True)
    
    def player(self, game):
        # Convert board to tensor: current player = 1, opponent = -1
        board_tensor = torch.tensor(
            [piece if piece == 0 else (1 if piece == game.current_player else -1) 
                for row in game.board for piece in row],
            dtype=torch.float32
        ).unsqueeze(0)
        #unsqueeze turns it into [1, tensor]. This allows passing in a whole batch of inputs
        
        # Get network output
        with torch.no_grad():
            net_output = self.net(board_tensor)
        value_head = net_output[0, 0].item()
        policy_output = net_output[0, 1:]
        
        # Find best valid move
        valid_moves = game.valid_moves()
        if not valid_moves:
            return None, value_head
        best_move = None
        best_policy_value = float('-inf')
        for move in valid_moves:
            move_index = move[0] * game.board_size + move[1]
            policy_value = policy_output[move_index].item()
            if policy_value > best_policy_value:
                best_policy_value = policy_value
                best_move = move
        
        #convert value head to our format between -1 and 1
        value_interpreted = (value_head*2 - 1)*game.current_player
        
        return best_move, value_interpreted

#endregion


#region indev (net, network training, genetic training)

class NeuralNet(nn.Module): #normal layers
    #the choice of layers in here seems arbitrary
    #0th output neuron is the value head, which will be initialized to compute the mean of the observations (the absolute piece advantage)

    @classmethod #I think I can call this instead of init?
    def load_or_create(cls, n_observations=64, n_actions=65, filename=None):
        """Load network from file if it exists, otherwise create a new one."""
        if filename is not None and os.path.exists(filename):
            net = torch.load(filename, weights_only=False) #doing this special stuff doesn't allow weights_only=True
            print(f"Loaded network from {filename}")
        else:
            net = cls(n_observations, n_actions, filename = filename)
            net.save(filename)
        return net

    def __init__(self, n_observations, n_actions, filename = None):
        super(NeuralNet, self).__init__() #calls initilization of nn.Module
        #https://www.sagarnildas.com/blogs/alpha-zero-tic-tac-toe-part-1-training-the-model
            #uses convolutional layers, might be useful
        self.input = nn.Linear(n_observations, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 64)
        self.output = nn.Linear(64, n_actions + 1) #+1 for value head, which will be at index 0
        self.filename = filename
        self.uuid = uuid.uuid4()

    def forward(self, x):
        x = F.relu(self.input(x)) #(Rectified Linear Unit) outputs max(0, x) - zeros out negative values
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = torch.sigmoid(self.output(x)) #1/(1+e^-x), squashes values to range [0, 1]
        return x
    
    def save(self, filename="unnamed_net.pt"):
        torch.save(self, filename)
        print(f"Saved network to {filename}")

class NeuralNetConvolutional(nn.Module): #convolutional layers

    @classmethod #I think I can call this instead of init?
    def load_or_create(cls, n_observations=BOARD_SIZE**2, n_actions=BOARD_SIZE**2+1, filename="net_new.pt"):
        """Load network from file if it exists, otherwise create a new one."""
        if filename is not None and os.path.exists(filename):
            net = torch.load(filename, weights_only=False) #doing this special stuff doesn't allow weights_only=True
            print(f"Loaded network from {filename}")
        else:
            net = cls()
            torch.save(net, filename)
        return net

    def __init__(self):
        super(NeuralNetConvolutional, self).__init__()

        # input = 6x6 board
        # convert to 5x5x16
        self.conv1 = nn.Conv2d(1, 16, kernel_size=2, stride=1, bias=False)
        # 5x5x16 to 3x3x32
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, bias=False)

        # compute output size dynamically
        with torch.no_grad():
            dummy = torch.zeros(1, 1, BOARD_SIZE, BOARD_SIZE)
            out = self.conv2(self.conv1(dummy))
            self.flat_size = out.numel()
        # self.size=3*3*32
        
        # the part for actions
        num_actions = BOARD_SIZE ** 2
        self.fc_action1 = nn.Linear(self.flat_size, self.flat_size // 4)
        self.fc_action2 = nn.Linear(self.flat_size // 4, num_actions)
        
        # the part for the value function
        self.fc_value1 = nn.Linear(self.flat_size, self.flat_size//6)
        self.fc_value2 = nn.Linear(self.flat_size//6, 1)
        self.tanh_value = nn.Tanh()
        
    def forward(self, x):

        #I don't really want to pass 4 dim stuff all the time, so let's convert
        if x.dim() == 1:
            # (N*N) → (1, 1, N, N)
            N = int(x.numel() ** 0.5)
            x = x.view(1, 1, N, N)
        elif x.dim() == 2:
            # (batch, N*N) → (batch, 1, N, N)
            batch = x.size(0)
            N = int(x.size(1) ** 0.5)
            x = x.view(batch, 1, N, N)
        elif x.dim() == 3:
            # (batch, 1, N*N) → (batch, 1, N, N)
            batch = x.size(0)
            N = int(x.size(2) ** 0.5)
            x = x.view(batch, 1, N, N)
        elif x.dim() == 4:
            # Already correct
            N = x.size(-1)

        y = F.leaky_relu(self.conv1(x))
        y = F.leaky_relu(self.conv2(y))
        y = y.view(-1, self.flat_size)
        
        # action head
        a = self.fc_action2(F.leaky_relu(self.fc_action1(y)))
        
        avail = (torch.abs(x.squeeze())!=1).type(torch.FloatTensor)
        avail = avail.reshape(-1, BOARD_SIZE**2)
        maxa = torch.max(a)
        exp = avail*torch.exp(a-maxa)
        prob = exp/torch.sum(exp)
        
        # value head
        value = self.tanh_value(self.fc_value2(F.leaky_relu( self.fc_value1(y) )))

        output = torch.cat([value, prob], dim=1)
        return output

#batch_size is the number of games to play in the batch, running full agent for each move of the games
def train_network(net, game, agent=None, batch_size=1, training_batches=1, learning_rate=0.001):
    
    # training_steps = number of times it should play a game against itself
    # mcts_iterations is number of nodes to explore with MCTS (each node is not full game due to value head rollout = "net")

    optimizer = torch.optim.Adam(net.parameters(), lr=learning_rate) #idk what this does
    move_count = 0
    
    for batch in range(training_batches):
        trajectory = []  #list of (board_tensor, policy_target, current_layer) tuples, one for each move of the game of this training step. Game state plus what decision was made, expressed as ideal policy head
        for _ in range(batch_size):
            game.reset()
            
            # Self-play: run mcts each move, record chosen move as "correct" (build trajectory list)
            while game.winner is None:
                # Convert board to tensor, self pieces are 1, opponent are -1
                board_tensor = torch.tensor(
                    [piece*game.current_player for row in game.board for piece in row], 
                    dtype=torch.float32
                )
                
                # Run agent to get chosen move
                result = agent.player(game)
                move = None
                valuation = None
                choices = None
                avg_depth = None
                try:
                    move = result[0]
                    valuation = result[1]
                    choices = result[2] #[(move, valuation)]
                    avg_depth = result[3]
                except IndexError:
                    debug=1 
                
                move_count += 1
                print(f"Self-Play Training Progress: {move_count/((BOARD_SIZE**2-5)*training_batches*batch_size)*100:.2f}%", end="\r", flush=True)

                # Create policy target (what we'd prefer the output to look like
                    #if we get a distribution from the agent, use that. Otherwise all 0s except chosen move = 1
                policy_target = torch.zeros(n_actions)
                if choices is not None:
                    for choice in choices: #choices is [move, weight]
                        policy_target[choice[0][0] * game.board_size + choice[0][1]] = choice[1]
                    if policy_target.sum() == 0: #if all moves are losing, be ambivalent over valid moves
                        for choice in choices:
                            policy_target[choice[0][0] * game.board_size + choice[0][1]] = 1/len(choices)
                else:
                    policy_target[move[0] * game.board_size + move[1]] = 1
                #normalize
                policy_target = policy_target/policy_target.sum() #<this is good, but policy_target = F.normalize(policy_target, p=1, dim=0) still has small values
                
                # print(policy_target.T) #a lot of the time the sum is zero (and thus all valid moves weighted equally)
                trajectory.append((board_tensor, policy_target, game.current_player))
                game.make_move(*move)
        
        # Train on trajectory
        loss_sum = 0
        for board_tensor, policy_target, current_player in trajectory:
            #actuals coming out of current net
            net_output = net(board_tensor.unsqueeze(0))
            value_pred = net_output[0, 0] 
            policy_pred = net_output[0, 1:]
            # print(policy_pred)
            # we cannot zero out invalid moves in policy_pred directly, but we can make a mask that will be used in policy_loss
            valid_mask = policy_target > 0 #create a tensor of 0s and 1s showing valid moves
            masked_policy_pred = policy_pred * valid_mask.float() #zero out invalid moves
            masked_policy_pred = masked_policy_pred / masked_policy_pred.sum() #normalize
            # print(masked_policy_pred)

            # Value loss: predict game outcome (-1, 0, 1) - relative to the player whose turn it was on that move
            value_target = torch.tensor(float(game.winner*current_player), dtype=torch.float32)
            value_loss = F.mse_loss(value_pred, value_target)
            # Policy loss: KL divergence or cross-entropy
            # policy_loss = F.kl_div(
            #     torch.log(policy_pred + 1e-8), 
            #     policy_target, 
            #     reduction='batchmean'
            # )
            policy_loss = F.mse_loss(masked_policy_pred, policy_target) 
                #idk how/if using masked_policy_pred (0ed invalid moves) helps, but we'll try
                #mse is what alphaZero uses, so hopefully the best option
            policy_pred = net_output[0, 1:] #I don't know why this is here or how it works. In some situations changes it, in others it does not. Back when I was directly 0ing out and normalizing policy_pred, it changed policy_pred back to 0ed but unnormalized
            # print(policy_pred)

            # OTHER MATH OPTIONS (usable for both policy and value probably)
            # 1. Cross-Entropy Loss (for one-hot targets). CrossEntropyLoss expects raw logits, so you should remove the sigmoid activation from your network output layer or replace it with log_softmax.
                # policy_loss = F.cross_entropy(policy_pred.unsqueeze(0), policy_target.argmax().unsqueeze(0))
            # 2. Mean Squared Error Loss (for soft or one-hot targets). For complex games like chess or go.
                # policy_loss = F.mse_loss(policy_pred, policy_target)
            # 3. KL divergence - works with soft targets but can be unstable with one-hot targets
                # policy_loss = F.kl_div(torch.log(policy_pred + 1e-8), policy_target, reduction='batchmean')
            # 4. Negative Log-Likelihood Loss (NLLLoss). Logs. Like cross-entropy but with logs.
                # policy_loss = F.nll_loss(something)
            
            loss = value_loss + policy_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            loss_sum += loss
        
        if batch % 1 == 0:
            print(f" Batch {batch}: Avg loss = {loss_sum/len(trajectory):.4f}")
        
        torch.save(net, "training_midMCTS.pt")
    #training done

def genetic_training(net, generations_count=10, population_size=10, keep_perc=0.2, games_count=100):
    """
    Possible variables:
        generations - kind of need this
        population - number of nets involved in the testing of each generatino
        we could try meshing agents together (sexual reproduction)
        % of population to kill off / keep
        keep a random agent or some others in the mix to keep them all grounded, like keep survivors of previous
        fight against each other or against random?
        start reducing guassian if survivors keep surviving?
        evaluation using policy or minimax with value_head
    """
    randomAgent = randomPlayer()
    best_winrates = dict()

    def generate_random_variants(base_net, num_variants, variation_std=1e-2):
        """
        Generate random variants of a NeuralNet instance by adding Gaussian noise to parameters.

        Args:
            base_net (NeuralNet): The original neural network instance to vary.
            num_variants (int): Number of variants to generate.
            variation_std (float): Standard deviation of Gaussian noise added to parameters.
                1e-4 to 5e-4 = minor fine-tuning
                1e-3 to 5e-3 = moderate changes
                1e-2 to more = risk of losing learned features, but big changes

        Returns:
            List[NeuralNet]: List of new NeuralNet instances with varied parameters.
        """
        variants = []
        for _ in range(num_variants):
            # Deep copy the base network to create a new variant
            variant_net = copy.deepcopy(base_net)
            variant_net.uuid = uuid.uuid4()
            # Add Gaussian noise to each parameter tensor
            with torch.no_grad():
                for param in variant_net.parameters():
                    noise = torch.randn_like(param) * variation_std
                    param.add_(noise)
            variants.append(variant_net)
        return variants

    old_survivors = [net]
    for generation_num in range(generations_count):
        print("Starting generation", generation_num, "of", generations_count-1)
        #create full population from survivors
        population = []
        population.extend(old_survivors)
        for parent in old_survivors:
            population.extend(generate_random_variants(parent, math.floor(population_size/len(old_survivors)), variation_std=4e-3))
        #evaluate population
        winrates = dict()
        for index, contestant in enumerate(population):
            minimaxAgent = minimax(max_depth = 2, valuation_method="value_head", net=contestant)
            results = GameMatch(minimaxAgent, randomAgent).play_n_games(games_count)
            winrates[contestant] = (results[minimaxAgent] + results[None]*0.5)/sum(results.values())
            print(f"Generation Eval Progress: {(index+1)/len(population)*100:.2f}%", end="\r", flush=True)
        
        #select survivors
        new_survivors = sorted(winrates, key=winrates.get, reverse=True)[:math.floor(len(population)*keep_perc)]
        print(f"Best winrate: {max(winrates.values())*100:.2f}%", " "*100)
        #see how many were from the old survivors
        count = sum(1 for item in new_survivors if item in old_survivors)
        retention = (count / len(new_survivors)) if new_survivors else 0
        #forget the old ones
        old_survivors = new_survivors
        #save off best one
        torch.save(old_survivors[0], "best_survivor.pt")

#endregion



#region actual execution
startTime = time.time() #in seconds since epoch

#AGENTS
# myNet = NeuralNet.load_or_create(n_observations, n_actions, filename = "best_survivor.pt")
# myNet = NeuralNet.load_or_create(n_observations, n_actions)
myNet = NeuralNetConvolutional.load_or_create(filename="mcts_valuehead_convolutional.pt")
netAgent = NeuralNetAgent(myNet)
minimaxTrainer = minimax(max_depth = 3, valuation_method="heuristic")
randomAgent = randomPlayer()
minimaxValueEvaluator = minimax(max_depth = 3, valuation_method="value_head", net=myNet)
mctsAgent = MCTSWithPUCT(myNet, iterations=1000, rollout_mode="value_head")

#RUN A SINGLE TURN
# mctsAgent.player(ReversiGame())
# print(netAgent.player(ReversiGame()))

#TRAINING
# genetic_training(myNet, generations_count=100, population_size=12, keep_perc=0.25, games_count=100)
# train_network(myNet, ReversiGame(), agent=mctsAgent, training_batches=100, batch_size=10)
# torch.save(myNet, "training.pt")

#VALUE EVAL
myMatch = GameMatch(
    #could run against MCTS as well, would be slow though
    minimaxValueEvaluator
    , randomAgent
    , printProgress=True
    , display=False)
myMatch.play_n_games(100) 
winrate = (myMatch.results[myMatch.agentA] + myMatch.results[None]*0.5)/sum(myMatch.results.values())
print(f"Value Win% = {winrate*100:.2f}%", " "*100)
# torch.save(myNet, f"value_{winrate:.3f}.pt")

#POLICY EVAL
myMatch = GameMatch(
    #could run against MCTS as well, would be slow though
    netAgent
    , randomPlayer()
    , printProgress=True)
myMatch.play_n_games(100) 
winrate = (myMatch.results[myMatch.agentA] + myMatch.results[None]*0.5)/sum(myMatch.results.values())
print(f"Policy Win% = {winrate*100:.2f}%")
# torch.save(myNet, f"policy_{winrate:.3f}.pt")

#MCTS EVAL
myMatch = GameMatch(
    #could run against MCTS as well, would be slow though
    mctsAgent
    , randomPlayer()
    , printProgress=True)
myMatch.play_n_games(100) 
winrate = (myMatch.results[myMatch.agentA] + myMatch.results[None]*0.5)/sum(myMatch.results.values())
print(f"MCTS Win% = {winrate*100:.2f}%")
# torch.save(myNet, f"policy_{winrate:.3f}.pt")

print("Time taken in seconds:", time.time() - startTime) 
#endregion


#region training results notes

# iteratinos=1000 gives average depth = 3.25

# minimax depth = 5 using heuristic had win rate of 68.5%, so that's a decent benchmark. If we can do better than that with nets, I'll be happy

# 8x8, starting blank net and rollout=heuristic. 4*5*1000, each training takes 12 minutes or so
# 1 = 0.497
# 2 = 0.632
# 3 = 0.692
# 4 = I think it got dramatically worse, but maybe we should push through it?

# 8x8, starting with rollout=pieces for the first couple trainings, 4*5*3000, with zeroing out and normalizing masked_policy_pred (for loss) and target_policy
# 0 = 45/49/6
# 1 = 636-328-40
# 2 = 711_246_43 (0.732)
# ATTEMPTS TO IMPROVE (there is a possibility we have a local maximum, so building off the 711 is not best, but why not try)
# zeroes, value_head = 434
# zeroes, random
# zeroes, policy_play 8 hours, 695_268_37 (0.714)
# zeroes, pieces = 526_436_38
# zeroes, heuristic = 539

# We can also do evals between agents, pick best ones, basically genetic manually

# 8x8 Training results (round of 10/100 training, win/loss/tie)
# 0 = 62/32/6
# 1 = 30/63/7 weird got worse
# 2 = 40/56/3
# 3 = 59/36/5
# 4 = 68/30/2
# 5 = 59/39/2 worse
# 6 = 59/38/1 saved off as 8_pieces
# switch to net valuation, but prior value net is badly/randomly trained. Also 4/4 batches
# 7 = 58/39/3
# 8 = 63/34/3
# 9 = 70/29/1
# 10 = 65/31/4 sad
# 11 = 56/43/1 why is it getting worse??
# 12 = 48/48/4
# increasing MCTS to 3000, batch 4*5


# 4x4 Training results (rounds of 10/100 training, win/loss/tie)
# 0 = 39/45/16
# 0 = 31/55/14
# 0 = 32/56/12
# 1 = 46/48/6
# 2 = 50/37/13
# 3 = 63/31/6
# 4 = 70/24/6
# 5 = 70/24/6 #loss has been 0 for a bit
# 6 = 66/23/11
# 7 = 71/24/5
# 7 trainings vs full solve is about even. Net 55/45
# STILL USING PIECES

# Agents list:
#     # MCTSWithPUCT(iterations=1000) #2 seconds
#       # pieces took 5 seconds for 100 games of 4x4
#       # random took 10 seconds for 100 games of 4x4
#       # net valuation took 20 seconds for 100 games of 4x4
#       # pieces took 10 seconds for 10 games of 8x8
#       # random took 288 seconds for 10 games of 8x8. Random player took 120 seconds?? Idk how this recording is working
#       # net valuation took 67 seconds for 100 games of 8x8. Somehow the random player took 97 seconds??!!
#     # minimax(max_depth=7) #2 seconds
#     # randomPlayer() #very fast
#     # NeuralNetAgent(net or filename) #very fast
#       # NeuralNetAgent(NeuralNet(n_observations, n_actions))
#     # HumanPlayer() #popup boxes for moves
#     # fullSolver() #only works for 4x4

#     #SPEED NOTES
#     #using debug I think, 20 minutes at mcts 1000 and minimax 8?, really?
#     #mcts 1000 and minimax 7 should be roughly equivalent compute load and seem equivalent at solving/competing
#     #run still has print, and is much faster than debug I think. 2 minutes for mcts1000 and minimax7

#endregion



