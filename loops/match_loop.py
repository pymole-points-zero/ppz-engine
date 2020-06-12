import config
from points import Points
from tensorflow.keras.models import load_model
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
        # inverse reward
        if self.args.candidate_turns_first:
            result = -result

        # выводим расположение файла с матчем и результат матча
        print(match_file_path, result, sep='\n')

    def match(self):
        # load candidate and best network weights
        candidate_model = load_model(self.args.candidate_weights)
        best_model = load_model(self.args.best_weights)

        # определяем, кто ходит первым
        if self.args.candidate_turns_first:
            first_model, second_model = candidate_model, best_model
        else:
            first_model, second_model = best_model, candidate_model

        # setup MCTS for both nets
        first_mcts = MCTS(self.args.simulations, first_model)
        second_mcts = MCTS(self.args.simulations, second_model)

        MCTSs = [first_mcts, second_mcts]

        game = Points(self.args.field_width, self.args.field_height)
        game.reset()

        # match neural networks
        while not game.is_ended:
            cur_mcts = MCTSs[game.player]
            cur_mcts.search(game)

            pi = cur_mcts.get_dirichlet_policy(game)

            # best action
            a = int(np.argmax(pi))

            game.auto_turn(a)

        first_mcts.exit.set()
        second_mcts.exit.set()

        return game
