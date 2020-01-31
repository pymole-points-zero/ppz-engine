from collections import deque
import gzip

import numpy as np

from utils.game import last_turn_player_reward, get_field_perc
from utils.processing.converting import moves_to_sgf
from points import Points
from mcts import MCTS
from neural import RNN
import config


class SelfplayLoop:
    def __init__(self, args):
        self.args = args

    def run(self):
        # start_time = time.time()

        game = Points(*self.args.field_size)

        # load training weights
        nnet = RNN.from_file(self.args.best_weights)

        self.generate_example(game, nnet)

        # print("Generated example for", (time.time() - start_time) / 3600, "hours")

    def generate_example(self, game, nnet):
        starting_position = game.reset(random_crosses=self.args.random_crosses)

        mcts = MCTS(self.args.example_simulations, nnet, c_puct=4)

        example = []

        # game loop
        while not game.is_ended:
            policy = mcts.get_policy(game)  # all actions' probabilities (not possible actions with 0 probability)
            # print('policy', policy)
            a = np.random.choice(len(policy), p=policy)

            # field, policy, value
            # don't have reward for now
            example.append([get_field_perc(game.field, game.player), policy, None])

            game.auto_turn(a)   # do action

        result = last_turn_player_reward(game)
        v = np.int8(result)

        # insert game reward to examples
        # for the last turned player (reward = v) for another (reward = -v)
        for position_index in range(len(example) - 1, -1, -1):
            example[position_index][2] = v
            v = -v

        if not config.RESULTS_FOLDER.exists():
            config.RESULTS_FOLDER.mkdir()

        # save sgf
        moves_to_sgf(starting_position,
                     (game.get_pos_of_ind(move) for move in game.moves),
                     config.RESULTS_FOLDER / 'selfplay.sgf',
                     result)

        # save training data
        np.save(config.RESULTS_FOLDER / 'training_data.npy', example)

