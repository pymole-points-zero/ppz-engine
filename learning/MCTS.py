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
		self.nnet = nnet
		self.Rsa = defaultdict(int)		# action Q
		self.Nsa = defaultdict(int)		# n times the state was visited
		self.N = defaultdict(int)
		self.P = {}						# inner policy for valid actions
		self.c_puct = c_puct

	def get_policy(self, game):
		# search calls
		for i in range(self.sim_count):
			self.game = copy.deepcopy(game)
			self.search()

		# policy distribution
		s = game.get_state()

		denom = self.N[s]
		policy = [0] * game.field_size

		for a in game.free_dots:
			child = (s, a)
			if child in self.Nsa:
				policy[a] = self.Nsa[child]/denom

		return np.array(policy)

	def search(self):
		s = self.game.get_state()

		if self.game.is_ended:
			# estimate after game scores from last player perspective
			# return to upper function negative reward because of player's turn change
			return last_turn_player_reward(self.game)

		if s not in self.P:
			# leaf node
			return -self.expansion(s)

		max_uct = -float('inf')
		for cur_a, cur_pi in self.P[s]:
			# print(curA, curPi, child_node, self.N)
			transit = (s, cur_a)
			if transit in self.Nsa:
				cur_uct = self.Rsa[transit]/self.Nsa[transit] + self.c_puct * cur_pi * sqrt(self.N[s])/(1 + self.Nsa[transit])
			else:
				cur_uct = self.c_puct * cur_pi * sqrt(self.N[s]+EPS)

			if cur_uct > max_uct:
				a = cur_a
				max_uct = cur_uct

		try:
			self.game.auto_turn(a)
		except:
			print(self.game)
			print(a)

			raise Exception
		# print(self.game, a)
		v = self.search()

		self.Rsa[(s, a)] += v
		self.Nsa[(s, a)] += 1
		self.N[s] += 1

		return -v

	def expansion(self, s):
		f = get_field_perc(self.game.field, self.game.player)

		Pi, v = self.nnet.predict(f)  # Possibility of each action and value of current game state

		self.P[s] = tuple(zip(self.game.free_dots, map(Pi.__getitem__, self.game.free_dots)))

		return v
