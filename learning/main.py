from utils import *
from coach import Coach
import os

args = dotdict({
	'iterations': 1,				# iterations (80)
	'examples': 2,				#
	'field_size': (15, 15),
	'history_length': 5,		# how much examples of iters will algorithm hold
	'example_simulations': 20,				# iters over MCTS
	'compare_simulations': 5,
	'compare_iters': 6,			# compare old and new net for n times
	'random_crosses': False,
	'examples_path': os.path.join('checkpoint', 'examples'),
	'update_threshold': 0.55
})


coach = Coach(args)
net = coach.selfplay()
net.save(name="best_model")