'''
That is Monte-Carlo Tree Search for my Dots project
The game is discribed in engine file
'''
from math import sqrt
import numpy as np
from logic import *
import copy
from collections import defaultdict

EPS = 1e-8


class MCTS:
	def __init__(self, sim_count, nnet, c_puct=1):
		'''All nodes are integers'''

		self.sim_count = sim_count
		self.game = None
		self.nnet = nnet
		self.R = defaultdict(int)		# action Q
		self.N = defaultdict(int)		# n times the state was visited
		self.P = {}						# inner policy for valid actions
		self.C = {}						# children
		self.c_puct = c_puct

		self.root = 0
		self.build_node(self.root)
		self.indexed_count = 0

	def build_node(self, node):
		f = get_field_perc(self.game.field, self.game.player)

		Pi, v = self.nnet.predict(f)  # Possibility of each action and value of current game state

		# TODO придумать, что сделать с этим листом, он ведь не будет изменяться
		self.P[node] = [(a, Pi[a]) for a in self.game.free_dots]
		self.C[node] = list(
			range(self.indexed_count, self.indexed_count + len(self.game.free_dots))
		)
		self.indexed_count += self.game.free_dots

		self.N[node] = 0

		return v

	def search(self, cur_node):
		if self.game.is_ended:
			# estimate after game scores from last player perspective
			# return to upper function negative reward because of player's turn change
			return last_turn_player_reward(self.game)

		if cur_node not in self.P:
			# leaf node
			v = self.build_node(cur_node)
			self.update(cur_node, v)

			return -v

		max_uct = -float('inf')
		for (curA, curPi), child_node in zip(self.P[cur_node], self.C[cur_node]):
			if cur_node in self.R:
				cur_uct = self.R[child_node]/self.N[child_node] + self.c_puct * curPi * sqrt(self.N[cur_node])/(1 + self.N[child_node])
			else:
				cur_uct = self.c_puct * curPi * sqrt(self.N[cur_node]+EPS)

			if cur_uct > max_uct:
				a = curA
				max_uct = cur_uct
				next_node = child_node

		self.game.auto_turn(a)

		v = self.search(next_node)

		self.update(cur_node, v)

		return -v

	def update(self, node, v):
		self.R[node] += v
		self.N[node] += 1

	def get_policy(self):
		denom = sum(self.N[child] for child in self.C[self.root])
		policy = [self.N[child]/denom for child in self.C[self.root]]
		return np.array(policy)

	def play_simulations(self, game):
		for _ in range(self.sim_count):
			self.game = copy.deepcopy(game)
			self.search(self.root)
