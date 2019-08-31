from engine import Game
from logic import *
import MCTS
import CNN
import copy
import numpy as np
import time
import pickle
import os
from utils import *


def learn(args, nnet = None):
	game = Game(5, 5)
	itermax, episode, his_len
	if nnet is None:
		nnet = CNN.DotsNet(game)
	trainHistory = []

	if not os.path.exists("checkpoint/"):
		os.mkdir("checkpoint/")
		os.mkdir("checkpoint/examples/")

	for i in range(args.itermax):
		iterExamples = []
		for e in range(episode):
			iterExamples += executeEpisode(game, nnet)

		# save examples of this iteration
		with open("checkpoint/examples/ex_i" + str(i) + ".txt", "wb") as file:
			pickle.dump(iterExamples, file)

		trainHistory.append(iterExamples)

		# if history is crowded then remove examples of oldest iteration
		if len(trainHistory) > his_len:
			trainHistory.pop(0)

		# save model's weights
		nnet.save(name='model'+str(i))

		# create backup
		old_nnet = CNN.DotsNet(game)
		old_nnet.load(name='model'+str(i))

		trainData = []
		for e in trainHistory:
			trainData += e
		np.random.shuffle(trainData)

		# train net
		nnet.train(trainData)

		# compare backup and trained net
		nnet = fight(old_nnet, nnet, game)

	return nnet

def executeEpisode(game, nnet):
	start = time.time()

	game.reset()
	mcts = MCTS.MCTS(25, nnet)

	examples = []
	while True:
		for _ in range(mcts.simNumb):
			sim = copy.deepcopy(game)
			mcts.search(sim)

		Pi = mcts.getVecPi(game)				# all actions' probabilities (not possible actions with 0 probability)

		# extend examples
		# dont have reward for now
		curPlrPercField = getFieldPerc(game.field, game.player)			# get field from player's percpective
		v_flip = np.flip(curPlrPercField, 0)		# create for processor time economy
		examples.extend([
			[curPlrPercField, Pi, None],
			[np.flip(curPlrPercField, 1), Pi, None],
			[v_flip, Pi, None],
			[np.flip(v_flip, 1), Pi, None]
		])

		a = np.random.choice(len(Pi), p=Pi)

		game.auto_turn(a)					# do action

		if game.gameEnded():				# episode ending
			v = lastTurnPlayerReward(game)
			# insert game reward to examples
			# for the last turned player (reward = v) for another (reward = -v)
			for g in range(len(examples) - 1, 2, -4):
				for e in range(4):
					examples[g-e][2] = v
				v = -v
			
			print(game.score[-1], game.score[1])
			print(time.time() - start)
			return examples

def fight(old_nnet, new_nnet, game):
	nnets = [old_nnet, new_nnet]
	duel_score = [0, 0]

	players = {
		-1: 0,
		1: 1
	}

	for i in range(2):
		players[-1], players[1] = players[1], players[-1]
			
		game.reset()
		while True:
			f = getFieldPerc(game.field, game.player)
			pi, _ = nnets[players[game.player]].predict(f)			# нам не нужна оценка игровой ситуации

			# нумеруем все действия и сортируем по значению
			pi = sorted(enumerate(pi), key=lambda p: p[1])
			a = len(pi) - 1
			# ищем свободное действие 
			while pi[a][0] in game.busy_dots:
				a -= 1
			a = pi[a][0]

			game.auto_turn(a)

			if game.gameEnded():
				if game.score[-1] > game.score[1]:
					duel_score[players[-1]] += 1
				elif game.score[-1] < game.score[1]:
					duel_score[players[1]] += 1
				break

	if duel_score[0] > duel_score[1]:
		print("Old net is winner")
		return nnets[0]
	elif duel_score[0] < duel_score[1]:
		print("New net is winner")
		return nnets[1]
	
	print("Draw")
	return new_nnet
# при поле 15 на 15 тренировочные данные одного эпизода весят примерно 2 МБ
# если выделить 800 МБ под примеры, то возможно одновременно хранить примеры 400 эпизодов
# один из вариантов - хранить последние 5 итераций, в каждой из которой по 80 эпизодов

args = {
	
}

net = learn(args)
net.save(name="best_model")

Game = Game(5, 5)
while 1:
	Game.reset()

	while not Game.gameEnded():
		if Game.turn % 2 == 1:
			Game.auto_turn(Game.get_ind_of_pos(*tuple(map(int, input().split()))))
		else:
			pred, _ = net.predict(Game.field)				# нам не нужна оценка игровой ситуации

			# нумеруем все действия и сортируем по значению
			pred = sorted(enumerate(pred), key=lambda p: p[1])
			a = len(pred) - 1
			# ищем свободное действие 
			while pred[a][0] in Game.busy_dots:
				a -= 1
			a = pred[a][0]

			Game.auto_turn(a)

		print(Game)

	print("GAME END: ", Game.score[-1], Game.score[1])
	# играем еще
	if input() == '0':
		break