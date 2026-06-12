#environment options
import gymnasium as gym #pip3 install gymnasium[classic_control]

#utilities
import math
import time
import sys
import random
from collections import namedtuple, deque
from itertools import count
import pickle #used to save objects to files
import matplotlib
import matplotlib.pyplot as plt #for rendering training chart

#ml stuff
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F




#------------CONFIGS-----------
BATCH_SIZE = 128 # BATCH_SIZE is the number of transitions sampled from the replay buffer
GAMMA = 0.99 # GAMMA is the discount factor as mentioned in the previous section
#epsilon is the probability of picking a random policy (truly random, not variation on working ones)
EPS_START = 0.9 # EPS_START is the starting value of epsilon
EPS_END = 0.05 # EPS_END is the final value of epsilon
EPS_DECAY = 1000 # EPS_DECAY controls the rate of exponential decay of epsilon, higher means a slower decay
TAU = 0.005 # TAU is the update rate of the target network
LR = 1e-4 # LR is the learning rate of the ``AdamW`` optimizer

num_episodes = 50 #I think this is the total number of games played, not that high actually. 500 got us to full perfection last time on cartpole
memory_capacity = 10000 #idk how this can be so big without causing problems, maybe it's never reached



#this is the game definition
env = gym.make("CartPole-v1") #fyi I think the environment is internally limited to 500 steps
# Get number of actions from gym action space
n_actions = env.action_space.n
# Get the number of state observations
state, info = env.reset()
n_observations = len(state)


#just helpful spec of how environments / game engines work
Transition = namedtuple('Transition',('state', 'action', 'next_state', 'reward'))
#holds recent observations qty=capacity
#the observations are of the form Transition
class ReplayMemory(object):

    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition"""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)
    

#initialized with only 3 layers, 128 nodes in between the observations and actions
#my guess is that "layers" means sets of connections, not nodes
class DQN(nn.Module):

    def __init__(self, n_observations, n_actions):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, x):
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)
    
policy_net = DQN(n_observations, n_actions)
target_net = DQN(n_observations, n_actions)
target_net.load_state_dict(policy_net.state_dict())
optimizer = optim.AdamW(policy_net.parameters(), lr=LR, amsgrad=True)
memory = ReplayMemory(memory_capacity)


steps_done = 0
def select_action(state):
    global steps_done
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
        math.exp(-1. * steps_done / EPS_DECAY)
    steps_done += 1
    if sample > eps_threshold:
        with torch.no_grad():
            # t.max(1) will return the largest column value of each row.
            # second column on max result is index of where max element was
            # found, so we pick action with the larger expected reward.
            return policy_net(state).max(1).indices.view(1, 1)
    else:
        return torch.tensor([[env.action_space.sample()]], dtype=torch.long)


def optimize_model():
    if len(memory) < BATCH_SIZE:
        return
    transitions = memory.sample(BATCH_SIZE)
    # Transpose the batch (see https://stackoverflow.com/a/19343/3343043 for
    # detailed explanation). This converts batch-array of Transitions
    # to Transition of batch-arrays.
    batch = Transition(*zip(*transitions))

    # Compute a mask of non-final states and concatenate the batch elements
    # (a final state would've been the one after which simulation ended)
    non_final_mask = torch.tensor(tuple(map(lambda s: s is not None,
                                          batch.next_state)), dtype=torch.bool)
    non_final_next_states = torch.cat([s for s in batch.next_state
                                                if s is not None])
    state_batch = torch.cat(batch.state)
    action_batch = torch.cat(batch.action)
    reward_batch = torch.cat(batch.reward)

    # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
    # columns of actions taken. These are the actions which would've been taken
    # for each batch state according to policy_net
    state_action_values = policy_net(state_batch).gather(1, action_batch)

    # Compute V(s_{t+1}) for all next states.
    # Expected values of actions for non_final_next_states are computed based
    # on the "older" target_net; selecting their best reward with max(1).values
    # This is merged based on the mask, such that we'll have either the expected
    # state value or 0 in case the state was final.
    next_state_values = torch.zeros(BATCH_SIZE)
    with torch.no_grad():
        next_state_values[non_final_mask] = target_net(non_final_next_states).max(1).values
    # Compute the expected Q values
    expected_state_action_values = (next_state_values * GAMMA) + reward_batch

    # Compute Huber loss
    criterion = nn.SmoothL1Loss()
    loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))

    # Optimize the model
    optimizer.zero_grad()
    loss.backward()
    # In-place gradient clipping
    torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
    optimizer.step()


# set up matplotlib for visualization
#only called in main loop
episode_durations = [] #sequential list of how long the cartpole stayed up each game. Used for printing/graph
plt.ion()
def plot_durations(show_result=False):
    plt.figure(1)
    durations_t = torch.tensor(episode_durations, dtype=torch.float)
    if show_result:
        plt.title('Result')
    else:
        plt.clf()
        plt.title('Training...')
    plt.xlabel('Episode')
    plt.ylabel('Duration')
    plt.plot(durations_t.numpy())
    # Take 100 episode averages and plot them too
    if len(durations_t) >= 100:
        means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
        means = torch.cat((torch.zeros(99), means))
        plt.plot(means.numpy())

    plt.pause(0.001)  # pause a bit so that plots are updated


#actually play the games / training!!
for i_episode in range(num_episodes):
    # Initialize the environment and get its state
    state, info = env.reset()
    state = torch.tensor(state, dtype=torch.float32).unsqueeze(0) #I don't know what this does, it modifies state, which seems cheating
    for t in count(): #I think this does steps until game end
        action = select_action(state)
        observation, reward, terminated, truncated, _ = env.step(action.item())
        reward = torch.tensor([reward])
        done = terminated or truncated

        if terminated:
            next_state = None
        else:
            next_state = torch.tensor(observation, dtype=torch.float32).unsqueeze(0)

        # Store the transition in memory, which is all the stuff returned from the environment, formatted by torch (except action maybe)
        memory.push(state, action, next_state, reward)

        # Move to the next state
        state = next_state

        # Perform one step of the optimization (on the policy network)
        optimize_model()

        # Soft update of the target network's weights
        # θ′ ← τ θ + (1 −τ )θ′
        target_net_state_dict = target_net.state_dict()
        policy_net_state_dict = policy_net.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key]*TAU + target_net_state_dict[key]*(1-TAU)
        target_net.load_state_dict(target_net_state_dict)

        if done:
            episode_durations.append(t + 1)
            plot_durations()
            break
        
        # print(t)
        # plt.pause(1) #pause to render the cartpole

#let the plot remain after code finishes
print('Complete')
plot_durations(show_result=True)
plt.ioff()
print("Close plot window to continue...")
plt.show() #freezes code until window is closed


# #demo final policy
# env = gym.make("CartPole-v1", render_mode="human") #don't know how to change render mode without remaking it. Human makes it continuously render
# state, info = env.reset()
# state = torch.tensor(state, dtype=torch.float32).unsqueeze(0) #I don't know what this does, it modifies state, which seems cheating
# for t in count(): #I think this does steps until game end
#     action = policy_net(state).max(1).indices.view(1, 1) #skip to just picking best action based on current policy net (which should be the optimized one, right?)
#     observation, reward, terminated, truncated, _ = env.step(action.item())
#     reward = torch.tensor([reward])
#     done = terminated or truncated

#     if terminated:
#         next_state = None
#     else:
#         next_state = torch.tensor(observation, dtype=torch.float32).unsqueeze(0)

#     # Move to the next state
#     state = next_state

#     if done:
#         break

#     # plt.pause(0.2) #pause 0.2 seconds between renders
#     print(t)
#     time.sleep(1/30)

# with open("export.pickle", "wb") as f:
#     pickle.dump(policy_net, f, protocol=pickle.HIGHEST_PROTOCOL)

# input("Press Enter to continue...")

