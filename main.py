from utils import *
from Coach import Coach
import CNN
from engine import Game

args = dotdict({
	'itermax': 1,				# iterations (80)
	'episodes': 1,				# 
	'field_size': (15, 15),
	'history_length': 5,		# how much examples of iters will algorithm hold
	'MCTSsims': 2,				# iters over MCTS
	'compareIters': 1,			# compare old and new net for n times
	'MCTSfight': 2,
	'random_crosses': False,
})


coach = Coach(args)
coach.continue_learn()
#net = coach.learn()
#net.save(name="best_model")