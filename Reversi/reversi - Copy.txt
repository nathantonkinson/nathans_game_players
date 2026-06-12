#region plan and todo
#We could add saving replays to the GameMatch
#CODE THESE
# MCTS (with PUCT)
# Training loop
# Replay buffer (optional but recommended)
#endregion

#region imports and autoconfig
import os
import copy
import math
import random
import time

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
#endregion

#region config
BOARD_SIZE = 4
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
    def __init__(self, agentA, agentB, board_size=BOARD_SIZE, display=False):
        #accepts classes with a function "player(game)" that output a move and an optional valuation of the position 
        self.agentA = agentA
        self.agentB = agentB
        self.board_size = board_size
        self.game = ReversiGame(self.board_size) #will reset this between each game
        self.results = defaultdict(int) #win/loss/tie counts
        self.computeTime = [0, 0]
        self.display = display
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
            print(game_num, "done")
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

#region stuff that should be usable to all agents and all varieties of games

class NeuralNet(nn.Module):
    #the choice of layers in here seems arbitrary
    #0th output neuron is the value head, which will be initialized to compute the mean of the observations (the absolute piece advantage)

    @classmethod #I think I can call this instead of init?
    def load_or_create(cls, n_observations, n_actions, filename="mcts_puct_net.pt"):
        """Load network from file if it exists, otherwise create a new one."""
        net = cls(n_observations, n_actions)
        if os.path.exists(filename):
            net.load_state_dict(torch.load(filename, weights_only=False)) #doing this special stuff doesn't allow weights_only=True
            print(f"Loaded network from {filename}")
        else:
            net.save(filename)
        return net

    def __init__(self, n_observations, n_actions):
        super(NeuralNet, self).__init__() #calls initilization of nn.Module
        self.input = nn.Linear(n_observations, 256)
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 64)
        self.output = nn.Linear(64, n_actions + 1) #+1 for value head, which will be at index 0

    def forward(self, x):
        x = F.relu(self.input(x)) #(Rectified Linear Unit) outputs max(0, x) - zeros out negative values
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = torch.sigmoid(self.output(x)) #1/(1+e^-x), squashes values to range [0, 1]
        return x
    
    def save(self, filename="mcts_puct_net.pt"):
        torch.save(self.state_dict(), filename)
        print(f"Saved network to {filename}")
    
    

#endregion

#region complete/finished players
class randomPlayer:
    def __init__(self):
        self.name = "Random Player"
        pass
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
    def __init__(self, max_depth=5):
        self.name = "Minimax: depth=" + str(max_depth) + ", val=basic piece"
        self.max_depth = max_depth

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
            return None, self.valuation_piece(game)
        
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

    def valuation_piece(self, game): #returns probability of win of player 1. For the moment will be manual, might make a neural net later to estimate this
        if game.winner is not None:
            return game.winner
        else:
            #returns a number between -1 and 1 based on piece count
            p1_count = sum(row.count(1) for row in game.board)
            p2_count = sum(row.count(-1) for row in game.board)
            return (p1_count - p2_count) / (p1_count + p2_count)

class MCTSWithPUCT:
    """Monte Carlo Tree Search with optional PUCT (netural net guidance).
    This is exactly (so says copilot) what alpha zero uses in actual execution"""
    
    def __init__(self, net=None, iterations=1000, rollout_mode="pieces"):
        #could do something where we get filename of net?? not yet that fancy
        net_text = "yes" if net is not None else "no"
        self.name = "MCTS-PUCT: net=" + net_text + ", iterations=" + str(iterations)
        self.net = net
        self.iterations = iterations
        self.rollout_mode = rollout_mode #pieces (for proportion of pieces) or random (make random moves until game end)

    class MCTSNode:
        def __init__(self, parent_class_instance, game_state, parent=None, move=None):
            self.game_state = game_state
            self.valid_moves = game_state.valid_moves()
            self.parent = parent
            self.move = move
            self.children = []
            self.visits = 0
            self.wins = 0
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
            
            # Normalize priors
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
                
            if self.net is None:
                if self.parent_class.rollout_mode == "random":
                    rollout_game = copy.deepcopy(self.game_state)
                    while rollout_game.winner is None:
                        moves = rollout_game.valid_moves()
                        move = random.choice(moves)
                        rollout_game.make_move(*move)
                    valuation = 1 if rollout_game.winner == self.root_player else 0
                    return valuation
                elif self.parent_class.rollout_mode == "pieces":
                    my_piece_count = sum(row.count(self.root_player) for row in self.game_state.board)
                    opponent_piece_count = sum(row.count(-self.root_player) for row in self.game_state.board)
                    return my_piece_count / (my_piece_count + opponent_piece_count) #returns 0 to 1, proportion of my pieces. Not that great of a singal for reversi in particular, but a decent start
            else:
                #estimate win/loss using value head. Value should be between 0 and 1. 
                board_tensor = torch.tensor(
                    [piece if piece == 0 else (1 if piece == self.game_state.current_player else -1) 
                        for row in self.game_state.board for piece in row],
                    dtype=torch.float32
                ).unsqueeze(0)
                with torch.no_grad():
                    net_output = self.net(board_tensor)
                value_head = net_output[0, 0].item()
                # policy_output = net_output[0, 1:]
                return value_head

        def backpropagate(self, result):
            self.visits += 1
            self.wins += result #result is 0 to 1 probability of win
            if self.parent:
                self.parent.backpropagate(result)

    def player(self, root_state):
        self.root_state = root_state
        root_node = self.MCTSNode(self, root_state)

        for _ in range(self.iterations):
            node = root_node

            # Selection
            while node.is_fully_expanded() and node.children:
                node = node.best_child()

            # Expansion
            if not node.is_fully_expanded():
                node = node.expand()

            # Simulation
            result = node.rollout()

            # Backpropagation
            node.backpropagate(result)

        best_child = root_node.best_child(c_param=0)
        valuation = root_state.current_player * (best_child.wins - (best_child.visits - best_child.wins)) / best_child.visits #change valuation into -1 to 1 (absolute)
        return best_child.move, valuation

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



#region indev



#we could separate search algorithms from valuation algorithms... idk


#mcts_iterations is how many MCTS games to run for each batch, training_steps is how many batches to train for, learning_rate is ...?
def train_network(net, game, mcts_iterations=100, training_steps=100, learning_rate=0.001):
    
    mctsAgent = MCTS(iterations = mcts_iterations)
    optimizer = torch.optim.Adam(net.parameters(), lr=learning_rate) #idk what this does
    
    for step in range(training_steps):
        game.reset()
        trajectory = []  # Store (state, mcts_policy, result) tuples
        
        # Self-play: generate training data
        while game.winner is None:
            # Convert board to tensor
            board_tensor = torch.tensor(
                [piece for row in game.board for piece in row], 
                dtype=torch.float32
            )
            
            # Run MCTS to get move and policy distribution
            move, _ = mctsAgent.player(game, iterations=mcts_iterations)
            
            # Create policy target (one-hot for MCTS-chosen move)
            policy_target = torch.zeros(n_actions)
            policy_target[move[0] * game.board_size + move[1]] = 1.0
            
            trajectory.append((board_tensor, policy_target))
            game.make_move(*move)
        
        # Train on trajectory
        for board_state, policy_target in trajectory:
            net_output = net(board_state.unsqueeze(0))
            
            value_pred = net_output[0, 0]
            policy_pred = net_output[0, 1:]
            
            # Value loss: predict game outcome (-1, 0, 1)
            value_target = torch.tensor(float(game.winner), dtype=torch.float32)
            value_loss = F.mse_loss(value_pred, value_target)
            
            # Policy loss: KL divergence or cross-entropy
            policy_loss = F.kl_div(
                torch.log(policy_pred + 1e-8), 
                policy_target, 
                reduction='batchmean'
            )
            
            loss = value_loss + policy_loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        if step % 10 == 0:
            print(f"Step {step}: Loss = {loss.item():.4f}")



#endregion



#region actual execution
startTime = time.time() #in seconds since epoch

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
# myMatch = GameMatch(
#     randomPlayer()
#     , MCTSWithPUCT(
#         net=NeuralNet.load_or_create(n_observations, n_actions, filename="mcts_puct_net.pt")
#         , iterations=1000, rollout_mode = "random"
#     )
#     , display=False)
# myMatch.play_n_games(10) 
# myMatch.display_results()

# myNet = NeuralNet.load_or_create(n_observations, n_actions, filename="mcts_puct_net.pt")
# train_network(myNet, ReversiGame(BOARD_SIZE), training_steps=10)
# torch.save(myNet, "mcts_puct_net.pt")

print("Time taken in seconds:", time.time() - startTime) 
#endregion
