import random
import json
import os
import numpy as np
from collections import defaultdict


# ─────────────────────────────────────────────
# BLACKJACK ENVIRONMENT
# ─────────────────────────────────────────────

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

#region game functions
def card_value(rank): #returns numerical value given single-digit string that represents card. Returns 11 for Ace (use as 1 is elsewhere)
    if rank in ("J", "Q", "K"):
        return 10
    elif rank == "A":
        return 11
    return int(rank)

def hand_value(hand): #counts aces as 11 unless bust
    total = sum(card_value(r) for r in hand)
    aces = hand.count("A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def has_usable_ace(hand): #bool if we have an ace(s) and do not bust by counting them as 11
    total = sum(card_value(r) for r in hand)
    aces = hand.count("A")
    if aces and total <= 21:
        return True
    return False

def new_deck(): #returns 52 card deck
    return [rank for rank in RANKS for _ in SUITS]
#endregion

class BlackjackEnv: #has reset, _state to get data, and step - take an action(1=hit, 0=stay) returns(state, reward, done)
    """
    A simplified Blackjack environment matching the OpenAI Gym Blackjack-v1 setup.

    State: (player_sum, dealer_showing, usable_ace)
    Actions: 0 = stick, 1 = hit
    Reward: +1 win, -1 lose, 0 draw
    """

    def reset(self):
        self.deck = new_deck()
        random.shuffle(self.deck)
        self.player = [self.deck.pop(), self.deck.pop()]
        self.dealer = [self.deck.pop(), self.deck.pop()]
        return self._state()

    def _state(self): #weird choice for things to return as state but ok
        return (
            hand_value(self.player),
            card_value(self.dealer[0]),
            has_usable_ace(self.player),
        )

    def step(self, action):
        """
        action: 1 = hit, 0 = stick
        Returns: (state, reward, done)
        """
        if action == 1:
            self.player.append(self.deck.pop())
            player_val = hand_value(self.player)
            if player_val > 21:
                return self._state(), -1, True
            return self._state(), 0, False

        #only way to get down here is with action=0=stay

        # Stick – dealer plays out
        while hand_value(self.dealer) < 17:
            self.dealer.append(self.deck.pop())

        player_val = hand_value(self.player)
        dealer_val = hand_value(self.dealer)

        if dealer_val > 21 or player_val > dealer_val:
            reward = 1
        elif player_val == dealer_val:
            reward = 0
        else:
            reward = -1

        return self._state(), reward, True


# ─────────────────────────────────────────────
# Q-LEARNING MODEL
# ─────────────────────────────────────────────

class QLearningAgent: #has no import usage??
    """
    Tabular Q-learning agent for Blackjack.

    State space: (player_sum 2-21, dealer_card 1-10, usable_ace True/False)
    Action space: {0: stick, 1: hit}

    """

    

    def __init__(self, learning_rate=0.1, discount=1.0, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.99995):
        self.lr = learning_rate #the weight we give to new information vs old information when updating our Q-table. 0 means we ignore new info, 1 means we ignore old info. Typically between 0 and 1, often around 0.1
        self.gamma = discount #the discount factor for future rewards. 0 means we only care about immediate rewards, 1 means we care about all future rewards equally. Typically between 0 and 1, often around 0.9 or 0.99
        self.epsilon = epsilon #the probability of taking a random action instead of the best known action. 0 means we always take the best known action, 1 means we always take a random action. Typically starts high and decays over time to encourage exploration early on and exploitation later.
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        # Q-table: state -> [Q(stick), Q(hit)]
        self.q = defaultdict(lambda: np.zeros(2)) #q is a dict where keys are states, and values are lists with two items [Q(stick), Q(hit)], the values are expected rewards of that choice, initialized to 0 for unseen states
            #default dict allows us to avoid checking if keys exist before referencing them, and automatically initializes them to a default value (in this case, np.zeros(2)) when accessed for the first time. 

    def choose_action(self, state, greedy=False):
        #greedy means we ignore epsilon and always take the best known action. Used for evaluation after training.
        if not greedy and random.random() < self.epsilon: #.random() returns a float in [0.0, 1.0)
            return random.randint(0, 1)
        return int(np.argmax(self.q[state]))

    def update(self, state, action, reward, next_state, done):
        # Update Q-table using the Q-learning formula:
        # Q(state, action) = Q(state, action) + lr * (reward + gamma * max(Q(next_state)) - Q(state, action))
        target = reward
        if not done:
            target += self.gamma * np.max(self.q[next_state]) #if not done assume result from making best future choices, using knowledge from our learning (0 if unseen state).
        error = target - self.q[state][action] #difference between predicted and actual
        self.q[state][action] += self.lr * error
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save(self, filepath="blackjack_model.json"):
        """Serialize Q-table to a JSON file."""
        serializable = {
            str(k): v.tolist() for k, v in self.q.items()
        }
        data = {
            "q_table": serializable,
            "epsilon": self.epsilon,
            "lr": self.lr,
            "gamma": self.gamma,
        }
        with open(filepath, "w") as f:
            json.dump(data, f)
        print(f"Model saved to '{filepath}' ({len(self.q)} states learned).")

    def load(self, filepath="blackjack_model.json"):
        """Load a Q-table from a JSON file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file '{filepath}' not found.")
        with open(filepath, "r") as f:
            data = json.load(f)
        self.epsilon = data.get("epsilon", self.epsilon_min)
        self.lr = data.get("lr", self.lr)
        self.gamma = data.get("gamma", self.gamma)
        self.q = defaultdict(lambda: np.zeros(2))
        for k, v in data["q_table"].items():
            # Keys are stored as strings like "(17, 10, True)"
            key = eval(k)
            self.q[key] = np.array(v)
        print(f"Model loaded from '{filepath}' ({len(self.q)} states).")


# ─────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────

def train(episodes=500_000, save_path="blackjack_model.json"):
    """
    Train the Q-learning agent and save the model.
    Prints a progress summary every 50,000 episodes.
    """
    env = BlackjackEnv()
    agent = QLearningAgent()

    wins = losses = draws = 0
    log_interval = 50_000

    print(f"Training for {episodes:,} episodes …\n")

    for ep in range(1, episodes + 1):
        state = env.reset()
        done = False

        while not done:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            agent.update(state, action, reward, next_state, done)
            state = next_state

        if reward == 1:
            wins += 1
        elif reward == -1:
            losses += 1
        else:
            draws += 1

        if ep % log_interval == 0:
            total = wins + losses + draws
            win_rate = wins / total * 100
            print(
                f"  Episode {ep:>8,}  |  "
                f"Win {win_rate:5.1f}%  "
                f"Lose {losses/total*100:5.1f}%  "
                f"Draw {draws/total*100:5.1f}%  |  "
                f"ε={agent.epsilon:.4f}"
            )
            wins = losses = draws = 0

    agent.save(save_path)
    print("\nTraining complete.\n")
    return agent


# ─────────────────────────────────────────────
# EVALUATION
# ─────────────────────────────────────────────

def evaluate(episodes=10_000, model_path="blackjack_model.json", verbose=False):
    """
    Load a trained model and play `episodes` games in greedy mode.
    Prints per-game details when verbose=True.
    Reports win/loss/draw rates at the end.
    """
    env = BlackjackEnv()
    agent = QLearningAgent()
    agent.load(model_path)

    wins = losses = draws = 0

    print(f"\nEvaluating over {episodes:,} games …\n")

    for ep in range(1, episodes + 1):
        state = env.reset()
        done = False
        actions_taken = []

        while not done:
            action = agent.choose_action(state, greedy=True)
            actions_taken.append("HIT" if action == 1 else "STICK")
            state, reward, done = env.step(action)

        if reward == 1:
            wins += 1
            outcome = "WIN"
        elif reward == -1:
            losses += 1
            outcome = "LOSE"
        else:
            draws += 1
            outcome = "DRAW"

        if verbose:
            player_val = hand_value(env.player)
            dealer_val = hand_value(env.dealer)
            print(
                f"Game {ep:>5}  |  "
                f"Player {player_val:>2}  Dealer {dealer_val:>2}  |  "
                f"Actions: {', '.join(actions_taken):<30}  |  {outcome}"
            )

    total = wins + losses + draws
    print(f"\n{'='*55}")
    print(f"  Results over {total:,} games")
    print(f"{'='*55}")
    print(f"  Wins:   {wins:>6,}  ({wins/total*100:5.1f}%)")
    print(f"  Losses: {losses:>6,}  ({losses/total*100:5.1f}%)")
    print(f"  Draws:  {draws:>6,}  ({draws/total*100:5.1f}%)")
    print(f"{'='*55}\n")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    MODEL_FILE = "blackjack_model.json"

    # ── 1. Train ──────────────────────────────
    trained_agent = train(episodes=500_000, save_path=MODEL_FILE)

    # ── 2. Evaluate (load from file) ──────────
    evaluate(episodes=10_000, model_path=MODEL_FILE, verbose=False)
