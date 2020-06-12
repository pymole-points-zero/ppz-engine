from math import sqrt
import numpy as np
from utils.game import last_turn_player_reward, field_perception
import copy
from collections import defaultdict
from neural.model import prepare_predict_on_batch, prepare_predict
import multiprocessing as mp
import threading
import sys
import traceback
import signal

EPS = 1e-8

# TODO c_puct
class MCTS:
	def __init__(self, model, sim_count, c_puct=4, alpha=0.05, dirichlet_impact=0.25):
		self.sim_count = sim_count
		self.Rsa = defaultdict(float)		# action Q
		self.Nsa = defaultdict(int)			# n times the state was visited
		self.N = defaultdict(int)
		self.P = {}
		self.c_puct = c_puct
		self.alpha = alpha
		self.dirichlet_impact = dirichlet_impact
		self.model = model

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
			self.search_iteration()

	def search_iteration(self):
		transitions = []

		while not self.game.is_ended:
			s = self.game.get_state()

			# leaf node
			if s not in self.P:
				value = self.expansion(s)
				self.backpropagation(transitions, -value)
				break

			max_uct = -float('inf')
			for cur_a, cur_p in self.P[s]:
				# Transition
				t = (s, cur_a)
				if t in self.Nsa:
					cur_uct = self.Rsa[t] / self.Nsa[t] + self.c_puct * cur_p * sqrt(self.N[s]) / (1 + self.Nsa[t])
				else:
					cur_uct = self.c_puct * cur_p * sqrt(self.N[s] + EPS)

				if cur_uct > max_uct:
					a = cur_a
					max_uct = cur_uct

			try:
				self.game.auto_turn(a)
			except Exception:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				traceback.print_tb(exc_traceback)
				traceback.print_exc()
				print()
				print(self.game)
				print(a)

				raise Exception

			transitions.append((s, a))

		if self.game.is_ended:
			# estimate after game scores from last player perspective
			# return to upper function negative reward because of player's turn change
			value = last_turn_player_reward(self.game)
			self.backpropagation(transitions, value)

	def expansion(self, s):
		f = field_perception(self.game.points, self.game.owners, self.game.player)

		policy, value = prepare_predict(self.model, f)
		self.P[s] = tuple((move, policy.__getitem__(move)) for move in self.game.free_dots)

		return value

	def backpropagation(self, transitions, value):
		for s, a in reversed(transitions):
			self.Rsa[(s, a)] += value
			self.Nsa[(s, a)] += 1
			self.N[s] += 1
			value = -value


# TODO root parallelization
# TODO add option to delete all node except root and its children to release memory
# TODO get optimal alpha value

# flags
START_SEARCH = 0
SYNCHRONIZATION = 1
CACHED_PREDICTION = 2
PREDICTION_DATA = 3
DONE = 4


class MCTSRootParallelizer:
	def __init__(self, model, sim_count, c_puct=4, alpha=0.05, dirichlet_impact=0.25):
		self.model = model

		self.Rsa = defaultdict(int)		# Q reward of root actions
		self.Nsa = defaultdict(int)		# times action played
		self.N = defaultdict(int)
		#
		# self.c_puct = c_puct
		self.alpha = alpha
		self.dirichlet_impact = dirichlet_impact

		# create workers before any searches
		self.workers_count = mp.cpu_count()
		self.workers_rsa = [{} for _ in range(self.workers_count)]
		self.workers_nsa = [{} for _ in range(self.workers_count)]
		self.workers_n = [{} for _ in range(self.workers_count)]
		self.predictions = {}  # cached policy and value of workers' predictions
		self.workers = []
		self.conns = []

		exit = mp.Event()
		signal.signal(signal.SIGINT, lambda sig, frame: exit.set())

		for worker_id in range(self.workers_count):
			parent_conn, worker_conn = mp.Pipe()
			worker = mp.Process(target=MCTSRootWorker, args=(
				worker_id, self.workers_count, worker_conn, exit, sim_count,
				c_puct, alpha, dirichlet_impact,
			))
			worker.start()

			self.workers.append(worker)
			self.conns.append(parent_conn)

	def search(self, game):
		root_state = game.get_state()

		# send start search command to all workers
		for conn in self.conns:
			conn.send((START_SEARCH, (game,)))

		# prediction vars
		connection_timeout = 0.005
		state_waiters = defaultdict(list)
		fields = {}
		available_moves = {}

		done = [False] * self.workers_count

		while not all(done):
			ready_conns = mp.connection.wait(self.conns, connection_timeout)

			synchronization_conns = []

			for conn in ready_conns:
				flag, data = conn.recv()
				print("FLAG:", flag, "DATA:", data, file=sys.stderr)

				# worker synchronization
				if flag == SYNCHRONIZATION:
					worker_id, rsa, nsa, n = data

					self.update_master(worker_id, rsa, nsa, n)

					synchronization_conns.append(conn)

				# worker requests policy
				elif flag == CACHED_PREDICTION:
					state = data
					prediction = self.predictions.get(state, None)

					# prediction is not cached, request prediction data to start model
					if prediction is None:
						state_waiters[state].append(conn)

						# only one of waiter need to provide field data
						if len(state_waiters[state]):
							conn.send((CACHED_PREDICTION, None))

					# send cached prediction
					else:
						conn.send((CACHED_PREDICTION, prediction))

				# collect prediction data
				elif flag == PREDICTION_DATA:
					state, field, moves = data
					available_moves[state] = moves
					fields[state] = field

				# worker played simulations
				elif flag == DONE:
					worker_id = data
					done[worker_id] = True

			# TODO send to all except one
			if synchronization_conns:
				# TODO maybe store in self.Rsa, self.Nsa, self.N only root?
				Rsa = {}
				Nsa = {}
				for a in game.free_dots:
					t = (root_state, a)
					if t in self.Rsa:
						Rsa[t] = self.Rsa[t]
					if t in self.Nsa:
						Nsa[t] = self.Nsa[t]

				N = {root_state: self.N[root_state]}

				master_root = Rsa, Nsa, N

				for conn in synchronization_conns:
					conn.send((SYNCHRONIZATION, master_root))

			# TODO Ordered dict
			if fields:
				print(fields.keys())
				# TODO fix duplication
				for state, prediction in zip(list(fields.keys()), prepare_predict_on_batch(
						self.model, list(fields.values()))):
					policy, value = prediction
					policy = tuple((move, policy.__getitem__(move)) for move in available_moves[state])

					prediction = (policy, value)
					self.predictions[state] = prediction

					for conn in state_waiters[state]:
						conn.send((CACHED_PREDICTION, prediction))

					state_waiters.pop(state)
					available_moves.pop(state)
					fields.pop(state)

	def update_master(self, worker_id, rsa, nsa, n):
		# Recalculate master root. Subtract old values, and add new
		for key, value in rsa.items():
			self.Rsa[key] += value - self.workers_rsa[worker_id].get(key, 0)

		for key, value in nsa.items():
			self.Nsa[key] += value - self.workers_nsa[worker_id].get(key, 0)

		for key, value in n.items():
			self.N[key] += value - self.workers_n[worker_id].get(key, 0)

		# save new workers data
		self.workers_rsa[worker_id] = self.Rsa.copy()
		self.workers_nsa[worker_id] = self.Nsa.copy()
		self.workers_n[worker_id] = self.N.copy()

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


class MCTSRootWorker(MCTS):
	def __init__(self, worker_id, workers_count, conn, exit, sim_count, c_puct=4, alpha=0.05, dirichlet_impact=0.25):
		super().__init__(None, sim_count, c_puct, alpha, dirichlet_impact)
		self.worker_id = worker_id
		self.workers_count = workers_count
		self.conn = conn
		self.exit = exit
		print(self.worker_id, file=sys.stderr)

		self.messages = {}
		self.events = {}

		self.dispatcher = {
			START_SEARCH: self.start_search
		}

		self.search_thread = None

		self.listen_timeout = 0.005
		self.listen()

	def listen(self):
		while not self.exit.is_set() and not self.conn.closed:
			if self.conn.poll(timeout=self.listen_timeout):
				flag, data = self.conn.recv()
				if flag in self.events:
					self.events[flag].set()
				if flag in self.dispatcher:
					self.dispatcher[flag](*data)
				else:
					self.messages[flag] = data

	def start_search(self, game):
		# TODO shut down old search thread
		# if self.search_thread is not None:
		# 	self.search_thread
		search_thread = threading.Thread(target=self.search, args=(game,))
		search_thread.daemon = True
		search_thread.start()

	def search(self, game):
		root_state = game.get_state()
		# search calls
		for i in range(self.sim_count):
			self.game = copy.deepcopy(game)
			self.search_iteration()

			# each iteration synchronize
			root_Rsa = {}
			root_Nsa = {}
			for a in game.free_dots:
				t = (root_state, a)
				if t in self.Rsa:
					root_Rsa[t] = self.Rsa[t]
				if t in self.Nsa:
					root_Nsa[t] = self.Nsa[t]

			root_N = {root_state: self.N[root_state]}

			self.conn.send((SYNCHRONIZATION, (self.worker_id, root_Rsa, root_Nsa, root_N)))
			Rsa, Nsa, N = self.wait_flag(SYNCHRONIZATION)
			self.synchronize(Rsa, Nsa, N)

		self.conn.send((DONE, self.worker_id))

	def expansion(self, s):
		# check if prediction cached in master first
		self.conn.send((CACHED_PREDICTION, s))
		prediction = self.wait_flag(CACHED_PREDICTION)

		# master makes prediction
		if prediction is None:
			f = field_perception(self.game.points, self.game.owners, self.game.player)

			self.conn.send((PREDICTION_DATA, (s, f, self.game.free_dots)))
			prediction = self.wait_flag(CACHED_PREDICTION)

		# each of workers caches policy to reduce number of pipe messages
		policy, value = prediction
		self.P[s] = policy

		return value

	def synchronize(self, Rsa, Nsa, N):
		self.Rsa.update(Rsa)
		self.Nsa.update(Nsa)
		self.N.update(N)

	def wait_flag(self, flag):
		if flag in self.events:
			event = self.events[flag]
		else:
			event = threading.Event()
			self.events[flag] = event

		event.wait()
		self.events.pop(flag)
		return self.messages.pop(flag)