from utils.game import last_turn_player_reward, get_field_perc
from utils.processing.converting import save_sgf
from points import Points
from mcts import MCTS
import config

import numpy as np
import gzip
from tensorflow.keras.models import load_model


class SelfplayLoop:
    def __init__(self, args):
        self.args = args

    def run(self):
        # start_time = time.time()
        game, example = self.generate_example()

        if not config.RESULTS_FOLDER.exists():
            config.RESULTS_FOLDER.mkdir()

        # save sgf
        config.RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
        sgf_path = str(config.RESULTS_FOLDER / 'selfplay.sgf')
        save_sgf(game, sgf_path)

        # save numpy training example in .gz
        example_path = str(config.RESULTS_FOLDER / 'training_data.npy.gz')
        with gzip.open(example_path, 'w') as f:
            np.save(f, example)

        # print result paths for client
        print(sgf_path, example_path, sep='\n')
        # print("Generated example for", (time.time() - start_time) / 3600, "hours")

    def generate_example(self):
        # load training weights
        model = load_model(self.args.weights)

        # создаем экземпляр игры
        game = Points(self.args.field_width, self.args.field_height)
        game.reset(random_crosses=self.args.random_crosses)

        mcts = MCTS(self.args.simulations, model, c_puct=4)

        fields = []
        policies = []

        # game loop
        while not game.is_ended:
            mcts.search(game)
            policy = mcts.get_policy(game)  # all actions' probabilities (not possible actions with 0 probability)
            # print('policy', policy)
            a = int(np.random.choice(len(policy), p=policy))

            # field, policy, value
            # don't have reward for now

            fields.append(get_field_perc(game.field, game.player))
            policies.append(policy)

            game.auto_turn(a)   # do action

        v = np.int8(last_turn_player_reward(game))

        # insert game reward to examples
        # for the last turned player reward = v for another reward = -v
        values = np.ndarray(shape=(len(fields),), dtype=np.int8)
        for position_index in range(len(fields) - 1, -1, -1):
            values[position_index] = v
            v = -v

        example = np.array(list(zip(fields, policies, values)), dtype=[
            ('field', 'i1', (game.width, game.height, 2)),
            ('policy', 'f8', (game.field_size,)),
            ('value', 'i1')
        ])

        return game, example
