from math import sqrt
import numpy as np
from utils.game import last_turn_player_reward, get_field_perc
import copy
from collections import defaultdict
from neural.model import prepare_predict

EPS = 1e-8


# TODO root parallelization
# TODO add option to delete all node except root and its children to release memory
# TODO get optimal alpha value
class MCTS:
	def __init__(self, sim_count, model, c_puct=1, alpha=0.05, dirichlet_impact=0.25):
		self.sim_count = sim_count
		self.model = model
		self.Rsa = defaultdict(int)		# action Q
		self.Nsa = defaultdict(int)		# n times the state was visited
		self.N = defaultdict(int)
		self.P = {}						# inner policy for valid actions
		self.c_puct = c_puct
		self.alpha = alpha
		self.dirichlet_impact = dirichlet_impact

	def get_policy(self, game):
		# policy distribution
		s = game.get_state()

		denom = self.N[s]
		policy = [0] * game.field_size

		for a in game.free_dots:
			child = (s, a)
			if child in self.Nsa:
				policy[a] = self.Nsa[child] / denom

		return np.array(policy, dtype=np.float)

	def get_dirichlet_policy(self, game):
		policy = self.get_policy(game)

		available_moves = list(game.free_dots)

		# calculate dirichlet noise for possible actions
		d = np.random.dirichlet(np.full(len(available_moves), self.alpha))
		dirichlet_policy = (1 - self.dirichlet_impact) * policy[available_moves] + self.dirichlet_impact * d

		# insert dirichlet noise to prior policy
		np.put(policy, available_moves, dirichlet_policy)

		return policy

	def search(self, game):
		# search calls
		for i in range(self.sim_count):
			self.game = copy.deepcopy(game)
			self.search_recursive()

	def search_recursive(self):
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
		except Exception:
			print(self.game)
			print(a)

			raise Exception

		# print(self.game, a)
		v = self.search_recursive()

		self.Rsa[(s, a)] += v
		self.Nsa[(s, a)] += 1
		self.N[s] += 1

		return -v

	def expansion(self, s):
		f = get_field_perc(self.game.field, self.game.player)

		Pi, v = prepare_predict(self.model, f)  # Possibility of each action and value of current game state

		self.P[s] = tuple(zip(self.game.free_dots, map(Pi.__getitem__, self.game.free_dots)))

		return v
