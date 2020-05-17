import numpy as np

from utils.game import last_turn_player_reward, get_field_perc
from utils.processing.converting import save_sgf
from points import Points
from mcts import MCTS
from neural import RNN
import config


class SelfplayLoop:
    def __init__(self, args):
        self.args = args

    def run(self):
        # start_time = time.time()
        game, example = self.generate_example()

        if not config.RESULTS_FOLDER.exists():
            config.RESULTS_FOLDER.mkdir()

        # сохраняем sgf игры
        config.RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
        sgf_path = str(config.RESULTS_FOLDER / 'selfplay.sgf')
        save_sgf(game, sgf_path)

        # сохраняем файл тренировочных данных
        example_path = str(config.RESULTS_FOLDER / 'training_data.npy')
        np.save(example_path, example)

        # печатаем информацию о том, куда сохранены результаты
        print(sgf_path, example_path, sep='\n')
        # print("Generated example for", (time.time() - start_time) / 3600, "hours")

    def generate_example(self):
        # load training weights
        nnet = RNN.from_file(self.args.weights)

        # создаем экземпляр игры
        game = Points(*self.args.parameters['field_size'])
        starting_position = game.reset(random_crosses=self.args.parameters['random_crosses'])

        mcts = MCTS(self.args.parameters['example_simulations'], nnet, c_puct=4)

        example = []

        # game loop
        while not game.is_ended:
            policy = mcts.get_policy(game)  # all actions' probabilities (not possible actions with 0 probability)
            # print('policy', policy)
            a = int(np.random.choice(len(policy), p=policy))

            # field, policy, value
            # don't have reward for now
            example.append([get_field_perc(game.field, game.player), policy, None])

            game.auto_turn(a)   # do action

        v = np.int8(last_turn_player_reward(game))

        # insert game reward to examples
        # for the last turned player reward = v for another reward = -v
        for position_index in range(len(example) - 1, -1, -1):
            example[position_index][2] = v
            v = -v

        return game, example
