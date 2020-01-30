import config
from points import Points
from neural import RNN
from mcts import MCTS
import numpy as np

from utils.processing.converting import moves_to_sgf


class MatchLoop:
    def __init__(self, args):
        self.args = args

    def run(self):
        # load candidate and best network weights
        candidate_nnet = RNN.from_file(self.args.candidate_weights)
        best_nnet = RNN.from_file(self.args.best_weights)

        # compare nets
        if self.args.cadidate_turns_first:
            res = self.match(candidate_nnet, best_nnet)
        else:
            res = self.match(best_nnet, candidate_nnet)

    def match(self, first_nnet, second_nnet):
        # setup MCTS for both nets
        first_mcts = MCTS(self.args.match_parameters.compare_simulations, first_nnet)
        second_mcts = MCTS(self.args.compare_simulations, second_nnet)

        MCTSs = (first_mcts, second_mcts,)

        game = Points(self.args)
        starting_position = game.reset(random_crosses=self.args.random_crosses)

        while True:
            # all actions' probabilities (not possible actions with 0 probability)
            pi = MCTSs[game.player].get_policy(game)

            # best action
            a = np.argmax(pi)

            game.auto_turn(a)

            if game.is_ended:
                break

        moves_to_sgf(starting_position,
                     (game.get_pos_of_ind(move) for move in game.moves),
                     config.RESULTS_FOLDER / 'match.sgf')

        if game.score[-1] > game.score[1]:
            return -1
        elif game.score[-1] < game.score[1]:
            return 1

        return 0
