from engine import Game
from logic import *
from MCTS import *
from utils import *
import CNN

import numpy as np
import time
import pickle
import os
import glob
import logging

# points to continue learn cycle
start_points = (
	'IterationStarted',
	'EpisodeStarted',
	'EpisodeEnded',
	'ExamplesSaveStarted',
	'ExamplesSaveEnded',
	'ExamplesDeleteStarted',
	'ExamplesDeleteEnded',
	'TrainStarted',
	'TrainEnded',
	'IterationEnded'
)

logging.basicConfig(
	filename="Coach.log",
	format='%(asctime)s - %(message)s', datefmt='%H:%M:%S',
	level=logging.INFO
)


class Coach:
	def __init__(self, args):
		self.args = args
		self.symmetries_per_turn = 8 if self.args.field_size[0] == self.args.field_size[1] else 4
		self.trainHistory = []

	def learn(self, nnet = None, continue_learning = False):
		learn_start = time.time()
		game = Game(*self.args.field_size)

		if continue_learning:
			nnet, start_iter = self.continue_learn(game)
		else:
			start_iter = 0
			self.trainHistory = []
			if nnet is None:
				nnet = CNN.DotsNet()
				# save first initiated nnet
				nnet.save(name='model0')

		# learn loop
		for i in range(start_iter, self.args.itermax):
			print('Iteration:', i)
			logging.info("IterationStarted" + str(i))

			for e in range(self.args.episodes):
				print('Episode:', e)
				logging.info("EpisodeStarted" + str(e))
				newExample = self.executeEpisode(game, nnet)

				# save each new example
				np.save("checkpoint/examples/ex" + str(e) + "_i" + str(i) + ".npy", newExample)

				logging.info("EpisodeEnded" + str(e))


			logging.info("ExamplesSaveStarted")

			# concatenate all examples of iteration and
			# save each example of iteration in hdf5 file
			iterExamples = np.empty(shape=[0, 3], dtype=np.object)
			example_names = glob.glob("checkpoint/examples/ex*_i" + str(start_iter) + ".npy")

			for ex_id, example_name in enumerate(example_names):
				try:
					example = np.load(example_name)
					iterExamples = np.append(iterExamples, values=example, axis=0)
				except:
					print(example_name, 'is broken')

			np.save('checkpoint/examples/iter' + str(start_iter) + '.npy', iterExamples)

			if len(iterExamples) > 0:
				self.trainHistory.append(iterExamples)

			logging.info('ExamplesSaveEnded')

			# then delete all examples
			logging.info("ExamplesDeleteStarted")

			for example_name in example_names:
				os.remove(example_name)

			logging.info("ExamplesDeleteEnded")

			# if history is crowded then remove examples of oldest iteration
			if len(self.trainHistory) > self.args.history_length:
				self.trainHistory.pop(0)

			# load backup
			old_nnet = CNN.DotsNet()
			old_nnet.load(name='model'+str(i))

			# shuffle examples
			trainData = [e for it in self.trainHistory for e in it]
			np.random.shuffle(trainData)

			# train net
			for ep in range(CNN.args.epochs):
				logging.info('TrainStarted' + str(ep))
				nnet.train(trainData)
				logging.info('TrainEnded' + str(ep))

			# compare backup and trained net
			fight_start = time.time()
			nnet = self.fight(old_nnet, nnet, game)
			# save best model as next iteration model
			nnet.save(name='model'+str(i + 1))
			print("Fighted for", time.time() - fight_start)

			logging.info("IterationEnded" + str(i))
		
		print("Learned for", (time.time() - learn_start)/3600, "hours")

		return nnet

	def executeEpisode(self, game, nnet):
		start = time.time()

		game.reset(random_crosses = self.args.random_crosses)
		mcts = MCTS(self.args.MCTSsims, nnet, c_puct=4)

		examples = []
		while True:
			mcts.play_simulations(game)
			pi = mcts.getVecPi(game)				# all actions' probabilities (not possible actions with 0 probability)

			a = np.random.choice(len(pi), p=pi)

			# extend examples
			# dont have reward for now
			# multiply examples by rotating them
			sym = getSymmetries(game, pi)
			for f, p in sym:
				examples.append([f, p, None])

			game.auto_turn(a)					# do action

			if game.gameEnded():				# episode ending
				print(game.score[-1], game.score[1])
				v = np.int8(lastTurnPlayerReward(game))

				# don't need draw examples
				if v == 0:
					print(time.time() - start)
					return []
				# insert game reward to examples
				# for the last turned player (reward = v) for another (reward = -v)
				for g in range(len(examples) - 1, self.symmetries_per_turn - 2, -self.symmetries_per_turn):
					for e in range(self.symmetries_per_turn):
						examples[g-e][2] = v
					v = -v

				examples = np.asarray(examples)
				print(time.time() - start)
				return examples

	def fight(self, old_nnet, new_nnet, game):
		# setup MCTS for both nets
		oldMCTS = MCTS(self.args.MCTSfight, old_nnet)
		newMCTS = MCTS(self.args.MCTSfight, new_nnet)

		nnets = [old_nnet, new_nnet]
		MCTSs = [oldMCTS, newMCTS]
		duel_score = [0, 0]

		players = {
			-1: 0,
			1: 1
		}

		for i in range(self.args.compareIters):
			players[-1], players[1] = players[1], players[-1]
				
			game.reset(random_crosses = self.args.random_crosses)
			while True:
				MCTSs[players[game.player]].play_simulations(game)
				pi = MCTSs[players[game.player]].getVecPi(game)			# all actions' probabilities (not possible actions with 0 probability)

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

		print("Old:", duel_score[0], ", New:", duel_score[1])
		if duel_score[0] > duel_score[1]:
			print("Old net is winner")
			return nnets[0]
		elif duel_score[0] < duel_score[1]:
			print("New net is winner")
			return nnets[1]
		
		print("Draw")
		return new_nnet

	def pretrain(self, nnet, examples_dir = "scraping/examples/"):
		# load examples
		if not os.path.exists(examples_dir):
			return
		
		# get batch of games
		for batch in self._load_examples(examples_dir):
			nnet.train(batch)

		return nnet

	def _load_examples(self, examples_dir):
		files = os.listdir(examples_dir)
		for file_name in files:
			with open(examples_dir+file_name, 'rb') as f:
				batch = pickle.load(f)
			yield batch

	def get_continue_params(self, log_name="Coach.log"):
		if not os.path.isfile(log_name):
			return None

		# get log
		with open(log_name, 'r') as file:
			log = file.read()

		# get messages from the log
		log = log.split('\n')[:-1]
		for i in range(len(log)):
			_, *message = log[i].split(' - ')
			message = ''.join(message)
			log[i] = message

		# find record of last iteration
		for i in log[::-1]:
			if 'IterationStarted' in i:
				break
		else:
			return None

		get_int = lambda x, y: int(x[len(y):])

		# get id of the iteration
		iteration_id = get_int(i, 'IterationStarted')

		i = -1
		start_from = ''
		while True:
			if len(log) < abs(i):
				return None
			last_record = log[i]

			for point in start_points:
				if point in last_record:
					start_from = point
					break

			if start_from != '':
				break

			i -= 1

		if start_from in ('EpisodeStarted', 'EpisodeEnded', 'TrainStarted', 'TrainEnded'):
			start_from = (start_from, get_int(last_record, start_from))

		print(start_from)
		return iteration_id, start_from

	def continue_learn(self, game):
		# this is the copy of the learn loop with continue learn logic
		params = self.get_continue_params()

		nnet = CNN.DotsNet()
		if params is None:
			return nnet, 0

		start_iter, continue_point = params
		if len(continue_point) == 2:
			continue_point, arg = continue_point

		# delete a broken file to prevent loading into history
		if os.path.isfile('checkpoint/examples/iter' + str(start_iter) + '.npy') and \
			start_points.index(continue_point) < start_points.index('ExamplesSaveEnded'):
			os.remove('checkpoint/examples/iter' + str(start_iter) + '.npy')

		# load examples
		if os.path.exists("checkpoint/examples/"):
			iter_files = glob.glob("checkpoint/examples/iter*")
			ex_count = min(len(iter_files), self.args.history_length)
			for i in range(len(iter_files) - ex_count, ex_count):
				try:
					iterExamples = np.load(iter_files[i])
					self.trainHistory.append(iterExamples)
				except:
					pass
		else:
			os.mkdir("checkpoint/")
			os.mkdir("checkpoint/examples/")

		# save first initiated nnet
		if start_iter == 0:
			if not os.path.isfile('checkpoint/models/model0.h5'):
				nnet.save(name='model0')
		else:
			# load model of current iteration
			if os.path.isfile('checkpoint/models/model' + str(start_iter) + '.h5'):
				nnet.load(name='model' + str(start_iter))

		# learn loop
		print('Iteration:', start_iter)

		if continue_point == 'IterationStarted':
			logging.info("IterationStarted" + str(start_iter))

		if start_points.index(continue_point) <= start_points.index('EpisodeEnded'):
			if continue_point == 'EpisodeStarted':
				e_start = arg
			elif continue_point == 'EpisodeEnded':
				e_start = arg + 1
			else:
				e_start = 0

			for e in range(e_start, self.args.episodes):
				print('Episode:', e)
				logging.info("EpisodeStarted" + str(e))
				newExample = self.executeEpisode(game, nnet)

				# save each new example
				np.save("checkpoint/examples/ex" + str(e) + "_i" + str(start_iter) + ".npy", newExample)

				logging.info("EpisodeEnded" + str(e))


		# save as one file
		if start_points.index(continue_point) < start_points.index('ExamplesSaveEnded'):
			if continue_point != 'ExamplesSaveStarted':
				logging.info('ExamplesSaveStarted')

			# concatenate all examples of iteration and
			# save each example of iteration in hdf5 file
			iterExamples = np.empty(shape=[0, 3], dtype=np.object)
			example_names = glob.glob("checkpoint/examples/ex*_i" + str(start_iter) + ".npy")

			for ex_id, example_name in enumerate(example_names):
				try:
					example = np.load(example_name)
					iterExamples = np.append(iterExamples, values=example, axis=0)
				except:
					print(example_name, 'is broken')

			np.save('checkpoint/examples/iter' + str(start_iter) + '.npy', iterExamples)

			if len(iterExamples) > 0:
				self.trainHistory.append(iterExamples)

			logging.info('ExamplesSaveEnded')

		# then delete all examples
		if start_points.index(continue_point) < start_points.index('ExamplesDeleteEnded'):
			if continue_point != 'ExamplesDeleteStarted':
				logging.info('ExamplesDeleteStarted')

			for example_name in example_names:
				os.remove(example_name)

			logging.info('ExamplesDeleteEnded')

		# if history is crowded then remove examples of oldest iteration
		if len(self.trainHistory) > self.args.history_length:
			self.trainHistory.pop(0)

		# load backup of the current model
		old_nnet = CNN.DotsNet()
		old_nnet.load(name='model'+str(start_iter))

		# shuffle examples
		trainData = [e for it in self.trainHistory for e in it]
		np.random.shuffle(trainData)

		# train net
		if start_points.index(continue_point) < start_points.index('TrainEnded'):
			if continue_point in ('TrainStarted', 'TrainEnded'):
				nnet.load(folder='checkpoint/', name='training_checkpoint')
				ep_start = arg + 1 if continue_point == 'TrainEnded' else arg
			else:
				ep_start = 0

			for ep in range(ep_start, CNN.args.epochs):
				logging.info('TrainStarted' + str(ep))
				nnet.train(trainData)
				logging.info('TrainEnded' + str(ep))
		else:
			# load trained nnet if train is ended
			nnet.load(folder='checkpoint/', name='training_checkpoint')

		# compare backup and trained net
		if start_points.index(continue_point) < start_points.index('IterationEnded'):
			fight_start = time.time()
			nnet = self.fight(old_nnet, nnet, game)

			# save best model as next iteration model
			nnet.save(name='model'+str(start_iter + 1))

			print("Fighted for", time.time() - fight_start)

			logging.info('IterationEnded' + str(start_iter))

		return nnet, start_iter + 1
