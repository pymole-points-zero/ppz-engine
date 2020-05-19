import config
from points import Points
from neural import RNN
from mcts import MCTS
import numpy as np

from utils.processing.converting import save_sgf


class MatchLoop:
    def __init__(self, args):
        self.args = args

    def run(self):
        # compare nets
        game = self.match()

        # сохраняем матч
        config.RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
        match_file_path = config.RESULTS_FOLDER / 'match.sgf'

        save_sgf(game, match_file_path)

        result = game.get_winner()

        # выводим расположение файла с матчем и результат матча
        print(match_file_path, result, sep='\n')

    def match(self):
        # load candidate and best network weights
        candidate_nnet = RNN.from_file(self.args.candidate_weights)
        best_nnet = RNN.from_file(self.args.best_weights)

        # определяем, кто ходит первым
        if self.args.candidate_turns_first:
            first_nnet, second_nnet = candidate_nnet, best_nnet
        else:
            first_nnet, second_nnet = best_nnet, candidate_nnet

        # setup MCTS for both nets
        first_mcts = MCTS(self.args.parameters['compare_simulations'], first_nnet)
        second_mcts = MCTS(self.args.parameters['compare_simulations'], second_nnet)

        MCTSs = {-1: first_mcts, 1: second_mcts}

        game = Points(*self.args.parameters['field_size'])

        # match neural networks
        while not game.is_ended:
            cur_mcts = MCTSs[game.player]
            cur_mcts.search(game)

            # all actions' probabilities (not possible actions with 0 probability)
            pi = cur_mcts.get_policy(game)

            # best action
            a = int(np.argmax(pi))

            game.auto_turn(a)

        return game
