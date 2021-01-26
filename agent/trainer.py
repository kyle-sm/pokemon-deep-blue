"""
The trainer module handles everything related to getting
training data and developing the model
"""
import logging
from functools import cache

import numpy as np
import torch as T
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class PolicyNetwork(nn.Module):
    def __init__(self, lr, input_dims, fc1_dims, fc2_dims, n_actions):
        super(PolicyNetwork, self).__init__()
        self.input_dims = input_dims
        self.lr = lr
        self.fc1_dims = fc1_dims
        self.fc2_dims = fc2_dims
        self.n_actions = n_actions
        self.fc1 = nn.Linear(*self.input_dims, self.fc1_dims)
        self.fc2 = nn.Linear(self.fc1_dims, self.fc2_dims)
        self.fc3 = nn.Linear(self.fc2_dims, self.n_actions)
        self.optimizer = T.optim.Adam(self.parameters(), lr=lr)

        self.device = T.device('cuda:0' if T.cuda.is_available() else 'cpu:0')
        self.to(self.device)

    def forward(self, observation):
        state = T.Tensor(observation).to(self.device)
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)

        return x


class PredictionNetwork(nn.Module):
    pass


class DynamicsNetwork(nn.Module):
    pass


class RepresentationNetwork(nn.Module):
    pass


class Agent():
    def __init__(self,
                 lr,
                 input_dims,
                 gamma=0.99,
                 n_actions=4,
                 l1_size=256,
                 l2_size=256):
        self.gamma = gamma
        self.reward_memory = []
        self.action_memory = []
        self.policy = PolicyNetwork(lr, input_dims, l1_size, l2_size,
                                    n_actions)

    def choose_action(self, observation):
        probabilities = F.softmax(self.policy.forward(observation))
        action_probs = T.distributions.Categorical(probabilities)
        action = action_probs.sample()
        log_probs = self.action_memory.append(log_probs)
        self.action_memory.append(log_probs)

        return action.item()

    def store_rewards(self, reward):
        self.reward_memory.append(reward)

    def learn(self):
        self.policy.optimizer.zero_grad()
        G = np.zeros_like(self.reward_memory, dtype=np.float64)
        for t in range(len(self.reward_memory)):
            G_sum = 0
            discount = 1
            for k in range(t, len(self.reward_memory)):
                G_sum += self.reward_memory[k] * discount
                discount *= self.gamma
            G[t] = G_sum
        mean = np.mean(G)
        std = np.std(G) if np.std(G) > 0 else 1
        G = (G - mean) / std

        G = T.tensor(G, dtype=T.float).to(self.policy.device)

        loss = 0
        for g, logprob in zip(G, self.action_memory):
            loss += -g * logprob

        loss.backward()
        self.policy.optimizer.step()

        self.action_memory = []
        self.reward_memory = []


class MonteCarloTree():
    def __init__(self, dynamics_function, prediction_function,
                 representation_function, action_size, observations):
        initial_state = representation_function.forward(observations)
        self.root = self.Node(initial_state)

    def search(self):
        pass

    class Node():
        def __init__(self, state, policy, value):
            self.state = state
            self.edges = []

        def expand(self):
            for _ in range(action_size):
                self.edges.append(Edge(0, 0, self.policy, 0, 0))

        @property
        def is_leaf(self):
            return len(self.edges) == 0

    class Edge():
        def __init__(self, visits, value, policy, reward, next_node):
            self.visits = visits
            self.value = value
            self.policy = policy
            self.reward = reward
            self.next_node = next_node

        def __gt__(self, other):
            return self.UCB() > other.UCB()

        def __lt__(self, other):
            return self.UCB() < other.UCB()

        @cache
        def UCB():
            return value + policy
            * ((sqrt(visits)/1 + visits))
            * (1.25 + math.log((visits + 19652 + 1)/19652)
