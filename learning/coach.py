from engine import Game
from MCTS import *
from learning import CNN

import numpy as np
import time
import pickle
import os
import glob
import logging
from collections import deque
from itertools import chain


# points to continue learn cycle
start_points = (
    'IterationStarted',
    'EpisodeStarted',
    'EpisodeEnded',
    'ExamplesSaveStarted',
    'ExamplesSaveEnded',
    'ExamplesDeleteStarted',
    'ExamplesDeleteEnded',
    'TrainStarted',
    'TrainEnded',
    'IterationEnded'
)

logging.basicConfig(
    filename="Coach.log",
    format='%(asctime)s - %(message)s', datefmt='%H:%M:%S',
    level=logging.INFO
)


class Coach:
    def __init__(self, args):
        self.args = args
        self.symmetries_per_turn = 8 if self.args.field_size[0] == self.args.field_size[1] else 4
        self.train_pool = deque([], maxlen=self.args.history_length)

    def selfplay(self, nnet=None, continue_learning=False):
        learn_start = time.time()

        if not os.path.exists(self.args.examples_path):
            os.makedirs(self.args.examples_path)

        game = Game(*self.args.field_size)

        self.trainHistory = []
        if nnet is None:
            nnet = CNN.DotsNet()
            # save first initiated nnet
            nnet.save(name='model0')

        # learn loop
        for i in range(self.args.iterations):
            print('Iteration:', i)
            logging.info("IterationStarted" + str(i))

            for e in range(self.args.examples):
                print('Episode:', e)
                logging.info("EpisodeStarted" + str(e))
                new_example = self.generate_example(game, nnet)

                # save each new example
                np.save(os.path.join(self.args.examples_path, f'ex{e}_i{i}.npy'), new_example)

                logging.info("EpisodeEnded" + str(e))

            logging.info("ExamplesSaveStarted")

            # concatenate all examples of iteration and
            # save each example of iteration
            iter_examples = np.empty(shape=[0, 3], dtype=np.object)
            example_names = glob.glob(os.path.join(self.args.examples_path, f'ex*_i{i}.npy'))

            for ex_id, example_name in enumerate(example_names):
                try:
                    example = np.load(example_name)
                    iter_examples = np.append(iter_examples, values=example, axis=0)
                except:
                    print(example_name, 'is broken')

            np.save(os.path.join(self.args.examples_path, f'iter{i}.npy'), iter_examples)

            # TODO no need to store training data in memory during example generation
            self.train_pool.append(iter_examples)

            logging.info('ExamplesSaveEnded')

            # then delete all examples
            logging.info("ExamplesDeleteStarted")

            for example_name in example_names:
                os.remove(example_name)

            logging.info("ExamplesDeleteEnded")

            # if history is crowded then remove examples of oldest iteration

            # load backup
            old_nnet = CNN.DotsNet()
            old_nnet.load(name='model' + str(i))

            # shuffle examples
            train_data = list(chain.from_iterable(self.train_pool))
            np.random.shuffle(train_data)

            # train net
            for ep in range(CNN.args.epochs):
                logging.info('TrainStarted' + str(ep))
                nnet.train(train_data)
                logging.info('TrainEnded' + str(ep))

            # compare backup and trained net
            fight_start = time.time()
            nnet = self.compare(old_nnet, nnet, game)
            # save best model as next iteration model
            nnet.save(name='model' + str(i + 1))
            print("Fighted for", time.time() - fight_start)

            logging.info("IterationEnded" + str(i))

        print("Learned for", (time.time() - learn_start) / 3600, "hours")

        return nnet

    def generate_example(self, game, nnet):
        start = time.time()

        game.reset(random_crosses=self.args.random_crosses)
        mcts = MCTS(self.args.example_simulations, nnet, c_puct=4)

        examples = []
        while True:
            Pi = mcts.get_policy(game)  # all actions' probabilities (not possible actions with 0 probability)
            # print('PI', Pi)
            a = np.random.choice(len(Pi), p=Pi)

            # extend examples
            # dont have reward for now
            # multiply examples by rotating them
            examples += ([f, p, None] for f, p in get_symmetries(game, Pi))

            game.auto_turn(a)   # do action

            if game.is_ended:  # episode ending
                print(game.score[-1], game.score[1])
                v = np.int8(last_turn_player_reward(game))

                # insert game reward to examples
                # for the last turned player (reward = v) for another (reward = -v)
                for g in range(len(examples) - 1, self.symmetries_per_turn - 2, -self.symmetries_per_turn):
                    for e in range(self.symmetries_per_turn):
                        examples[g - e][2] = v

                    v = -v

                print(time.time() - start)
                return np.asarray(examples)

    def compare(self, old_nnet, new_nnet, game):
        # setup MCTS for both nets
        oldMCTS = MCTS(self.args.compare_simulations, old_nnet)
        newMCTS = MCTS(self.args.compare_simulations, new_nnet)

        MCTSs = [oldMCTS, newMCTS]
        duel_score = [0, 0]

        players = {
            -1: 0,
            1: 1
        }

        for i in range(self.args.compare_iters):
            players[-1], players[1] = players[1], players[-1]

            game.reset(random_crosses=self.args.random_crosses)
            while True:
                pi = MCTSs[players[game.player]].get_policy(game)  # all actions' probabilities (not possible actions with 0 probability)

                # best action
                a = np.argmax(pi)

                game.auto_turn(a)

                if game.is_ended:
                    if game.score[-1] > game.score[1]:
                        duel_score[players[-1]] += 1
                    elif game.score[-1] < game.score[1]:
                        duel_score[players[1]] += 1
                    break

        print("Old:", duel_score[0], ", New:", duel_score[1])
        if duel_score[1]/self.args.compare_iters > self.args.update_threshold:
            print("New net is winner")
            return new_nnet

        print("Old net is winner")
        return old_nnet

    def pretrain(self, nnet, examples_dir="scraping/examples/"):
        # load examples
        if not os.path.exists(examples_dir):
            return

        # get batch of games
        for batch in self._load_examples(examples_dir):
            nnet.train(batch)

        return nnet

    def _load_examples(self, examples_dir):
        files = os.listdir(examples_dir)
        for file_name in files:
            with open(examples_dir + file_name, 'rb') as f:
                batch = pickle.load(f)
            yield batch
