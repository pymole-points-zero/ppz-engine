from math import sqrt
import numpy as np
from utils.game import last_turn_player_reward, field_perception
import copy
from collections import defaultdict
from neural.model import prepare_predict_on_batch, prepare_predict
import multiprocessing as mp
import threading

EPS = 1e-8


class MCTS:
	def __init__(self, model, sim_count, c_puct=4, alpha=0.05, dirichlet_impact=0.25):
		# TODO caching policy
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
			self.search_recursive()

	# TODO recursion -> loop
	def search_recursive(self):
		s = self.game.get_state()

		if self.game.is_ended:
			# estimate after game scores from last player perspective
			# return to upper function negative reward because of player's turn change
			return last_turn_player_reward(self.game)

		# get policy from model
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
			import sys, traceback
			exc_type, exc_value, exc_traceback = sys.exc_info()
			traceback.print_tb(exc_traceback)
			traceback.print_exc()
			print()
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
		f = field_perception(self.game.points, self.game.owners, self.game.player)

		policy, value = prepare_predict(self.model, f)
		self.P[s] = tuple((move, policy.__getitem__(move)) for move in self.game.free_dots)

		return value


# TODO root parallelization
# TODO add option to delete all node except root and its children to release memory
# TODO get optimal alpha value
class MCTSRootParallelizer:
	def __init__(self, sim_count, model, c_puct=4, alpha=0.05, dirichlet_impact=0.25):
		self.sim_count = sim_count
		self.model = model
		self.Rsa = defaultdict(int)		# action Q
		self.Nsa = defaultdict(int)		# n times the state was visited
		self.N = defaultdict(int)
		self.predictions = {}			# cached policy and value of all workers' predictions
		self.c_puct = c_puct
		self.alpha = alpha
		self.dirichlet_impact = dirichlet_impact

	def search(self, game):
		cpu_count = mp.cpu_count()

		# start MCTS workers and predictor threads
		workers = []
		conns = []
		results = []

		# for _ in range(cpu_count):
		# 	parent_conn, worker_conn = mp.Pipe()
		# 	worker = mp.Process(target=run_worker, args=(
		# 		worker_conn, game, self.sim_count, self.Rsa, self.Nsa,
		# 		self.N, self.c_puct, self.alpha, self.dirichlet_impact,
		# 	))
		# 	worker.start()
		# 	workers.append(worker)
		# 	conns.append(parent_conn)
		argss = []
		for _ in range(cpu_count):
			parent_conn, worker_conn = mp.Pipe()
			args=(
				worker_conn, game, self.sim_count, self.Rsa, self.Nsa,
				self.N, self.c_puct, self.alpha, self.dirichlet_impact,
			)
			argss.append(args)
			conns.append(parent_conn)

		predictor_thread = threading.Thread(target=run_predictor, args=(conns, self.model, self.predictions, results))
		predictor_thread.daemon = True
		predictor_thread.start()

		p = mp.Pool(cpu_count)
		p.starmap(run_worker, argss)

		# for worker in workers:
		# 	worker.join()

		# aggregate results
		for Rsa, Nsa, N in results:
			for key, value in Rsa.items():
				self.Rsa[key] += value
			for key, value in Nsa.items():
				self.Nsa[key] += value
			for key, value in N.items():
				self.N[key] += value

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


def run_predictor(conns, model, predictions, results):

	timeout = 0.005
	state_waiters = defaultdict(list)
	fields = {}
	available_moves = {}

	while True:
		ready_conns = mp.connection.wait(conns, timeout)

		for conn in ready_conns:
			flag, data = conn.recv()
			# worker ended search, get result and exit
			if flag == 0:
				results.append(data)
				conns.remove(conn)
			# if cached - send and if not then request field info
			elif flag == 1:
				# TODO only one of waiter need to provide field data
				state = data
				prediction = predictions.get(state, None)
				if prediction is None:
					state_waiters[state].append(conn)
					conn.send(None)
				else:
					conn.send(prediction)

			# collect prediction data
			elif flag == 2:
				state, field, moves = data
				available_moves[state] = moves
				fields[state] = field

			# TODO Ordered dict
			if fields:
				for state, prediction in zip(list(fields.keys()), prepare_predict_on_batch(model, list(fields.values()))):
					policy, value = prediction
					policy = tuple((move, policy.__getitem__(move)) for move in available_moves[state])

					prediction = (policy, value)
					predictions[state] = prediction

					for conn in state_waiters[state]:
						conn.send(prediction)

					state_waiters.pop(state)
					available_moves.pop(state)
					fields.pop(state)


def run_worker(conn, game, sim_count, Rsa, Nsa, N, c_puct, alpha, dirichlet_impact):
	mcts = MCTSRootWorker(conn, sim_count, Rsa, Nsa, N, c_puct, alpha, dirichlet_impact)
	mcts.search(game)

	# send result
	conn.send((0, (mcts.Rsa, mcts.Nsa, mcts.N)))


class MCTSRootWorker(MCTS):
	def __init__(self, conn, sim_count, Rsa, Nsa, N, c_puct=4, alpha=0.05, dirichlet_impact=0.25):
		super().__init__(None, sim_count, c_puct, alpha, dirichlet_impact)
		self.Rsa = Rsa		# action Q
		self.Nsa = Nsa		# n times the state was visited
		self.N = N
		self.conn = conn

	def expansion(self, s):
		# check if cached in predictor first
		self.conn.send((1, s))
		prediction = self.conn.recv()

		if prediction is None:
			# get
			f = field_perception(self.game.points, self.game.owners, self.game.player)

			# predictor worker make prediction and sends v
			self.conn.send((2, (s, f, self.game.free_dots)))
			prediction = self.conn.recv()

		# each of workers caches policy to reduce number of pipe messages
		policy, value = prediction
		self.P[s] = policy

		return value
