import time
import CNN
from engine import Game
from MCTS import MCTS

nnet = CNN.DotsNet()
game = Game(15, 15)
mcts = MCTS(10, nnet)


start = time.time()

mcts.play_simulations(game)
print(mcts.get_policy())

print(time.time() - start)

# 0.02
