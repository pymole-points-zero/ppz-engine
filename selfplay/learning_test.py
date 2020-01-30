import time
from learning import CNN
from learning.engine import Game
from MCTS import MCTS

nnet = CNN.DotsNet()
game = Game(15, 15)
game.reset()
mcts = MCTS(2, nnet, game.field_size)

start = time.time()

mcts.play_simulations(game)
print(mcts.get_policy())

print(time.time() - start)
