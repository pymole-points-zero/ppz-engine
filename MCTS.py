'''
That is Monte-Carlo Tree Search for my Dots project
The game is discribed in engine file
'''
from math import log, sqrt
import numpy as np
from engine import Game
from logic import *
import copy
import sys

EPS = 1e-8


class MCTS:
	def __init__(self, simNumb, nnet, c_puct=1):
		self.simNumb = simNumb
		self.nnet = nnet
		self.Nsa = {}				# stores times action a visited in state s
		self.Qsa = {}				# action Q
		self.Ns = {}				# n times the state s was visited
		self.P = {}					# inner policy for valid actions
		self.c_puct = c_puct

	def search(self, game):
		if game.is_ended():
			# estimate after game scores from last player perspective
			# return to upper function negative reward because of player's turn change
			return lastTurnPlayerReward(game)

		f = getFieldPerc(game.field, game.player)
		s = stringRepresentation(f)

		if s not in self.P:
			# leaf node
			Pi, v = self.nnet.predict(f)		# Possibility of each action and value of current game state

			self.P[s] = [(a, Pi[a]) for a in game.free_dots]
			self.Ns[s] = 0
			
			return -v

		max_uct = -float('inf')
		for curA, curPi in self.P[s]:
			if (s, curA) in self.Qsa:
				cur_uct = self.Qsa[s, curA] + self.c_puct * curPi * sqrt(self.Ns[s])/(1 + self.Nsa[(s, curA)])
			else:
				cur_uct = self.c_puct * curPi * sqrt(self.Ns[s]+EPS)

			if cur_uct > max_uct:
				a = curA
				max_uct = cur_uct

		game.auto_turn(a)

		v = self.search(game)

		if (s, a) in self.Qsa:
			self.Qsa[(s, a)] = (self.Qsa[(s, a)] * self.Nsa[(s, a)] + v)/(self.Nsa[(s,a)] + 1)
			self.Nsa[(s, a)] += 1
		else:
			self.Qsa[(s, a)] = v
			self.Nsa[(s, a)] = 1

		self.Ns[s] += 1

		return -v

	def getVecPi(self, game):
		f = getFieldPerc(game.field, game.player)
		s = stringRepresentation(f)

		denom = sum([self.Nsa[(s, a)] if (s, a) in self.Nsa else 0 for a in game.free_dots])
		vecPi = np.array([self.Nsa[(s, a)]/denom if (s, a) in self.Nsa else 0 for a in range(game.field_size)])
		return vecPi

	def play_simulations(self, game):
		for _ in range(self.simNumb):
			sim = copy.deepcopy(game)
			self.search(sim)
