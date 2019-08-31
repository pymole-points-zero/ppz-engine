import sys
from PyQt5.QtCore import (
    Qt,
    QBasicTimer
)
from PyQt5.QtGui import (
    QBrush,
    QPixmap
)
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QGraphicsTextItem,
    QGraphicsLineItem,
)

from engine import Game
import CNN
from logic import *
from MCTS import MCTS

FRAMES_MS           = 16      # ms/frame (62.5 frames per second)
SCREEN_WIDTH        = 800
SCREEN_HEIGHT       = 600
SOURCE_DIR          = 'source/'
SPRITES_DIR         = 'sprites/'

class Dot(QGraphicsPixmapItem):

    def __init__(self, x, y, parent = None):
        QGraphicsPixmapItem.__init__(self, parent)

        self.x = x
        self.y = y

class DotsGame(QGraphicsScene):
    def __init__(self, parent = None):
        QGraphicsScene.__init__(self, parent)
        
        # sprite system (actually not :)
        self.spr_dot_blue = QPixmap(SOURCE_DIR + SPRITES_DIR + 'dot_blue.png')
        self.spr_dot_red = QPixmap(SOURCE_DIR + SPRITES_DIR + 'dot_red.png')

        self.timer = QBasicTimer()
        self.timer.start(FRAMES_MS, self)

        self.game = Game(15, 15)
        self.game.reset(random_crosses=False)
        self.dots = [Dot(x, y) for y in range(self.game.height) for x in range(self.game.width)]
        self.scanCrosses()
        self.selected_dot = None

        self.nnet = CNN.DotsNet()
        self.nnet.load(folder = SOURCE_DIR + 'models/', name = 'm')
        self.mcts = MCTS(10, self.nnet, c_puct = 4)

        self.turn_order = {
            -1: 'player',
            1: self.nnet
        }

        self.cellSize = 16

        # add dots in scene
        for d in self.dots:
            d.setPos(d.x * self.cellSize, d.y * self.cellSize)
            self.addItem(d)

        # score label
        self.LScore = QGraphicsTextItem('0:0')
        self.addItem(self.LScore)
        self.LScore.setPos(SCREEN_WIDTH//2, 16)

        # lines container
        self.lines = []

        # view options
        self.view = QGraphicsView(self)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.show()
        self.view.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.setSceneRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)



    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            x = ev.scenePos().x()
            y = ev.scenePos().y()

            print(x, y)

            x, y = round(x/self.cellSize), round(y/self.cellSize)
            print(x, y)

            # inverse
            self.selected_dot = (x, y)

    def game_update(self):
        if self.selected_dot is not None:
            if self.game.can_put_dot(*self.selected_dot):
                # remember length of sur_zones before turn
                l = len(self.game.sur_zones)

                # player's turn
                dot_ind = self.game.get_ind_of_pos(*self.selected_dot)
                print(dot_ind)
                if self.doTurn(dot_ind):
                    return


                # nnet answer
                self.mcts.play_simulations(self.game)
                pi = self.mcts.getVecPi(self.game)

                # нумеруем все действия и сортируем по значению
                pi = sorted(enumerate(pi), key=lambda p: p[1])
                print('Policy:', pi)
                dot_ind = len(pi) - 1
                # ищем свободное действие 
                while pi[dot_ind][0] in self.game.busy_dots:
                    dot_ind -= 1
                dot_ind = pi[dot_ind][0]

                if self.doTurn(dot_ind):
                    return

                # add lines for surroundings
                for chain in self.game.sur_zones[l:]:
                    for i in range(len(chain) - 1):
                        coords = tuple(chain[i] + chain[i+1])
                        print(coords)
                        coords = tuple(c * self.cellSize for c in coords)

                        line = QGraphicsLineItem(*coords)
                        self.lines.append(line)
                        self.addItem(line)

                    # change score label text
                    self.LScore.setHtml(str(self.game.score[-1]) + ':' + str(self.game.score[1]))

            self.selected_dot = None

    def doTurn(self, dot_ind):
        # wrapper of game.auto_turn() function
        if self.game.player == -1:
            self.dots[dot_ind].setPixmap(self.spr_dot_blue)
        else:
            self.dots[dot_ind].setPixmap(self.spr_dot_red)

        self.game.auto_turn(dot_ind)

        if self.game.gameEnded():
            self.gameReset()
            return True

        return False

    def scanCrosses(self):
        for i in self.game.busy_dots:
            pos = self.game.get_pos_of_ind(i)
            if self.game.field[pos[0], pos[1], 0] == -1:
                self.dots[i].setPixmap(self.spr_dot_blue)
            else:
                self.dots[i].setPixmap(self.spr_dot_red)

    def gameReset(self):
        # wrapper of game.reset() function
        self.game.reset(random_crosses=True)
        self.scanCrosses()
        self.mcts = MCTS(50, self.nnet, c_puct = 2)

        # reset sprites of dots
        for d in self.dots:
            d.setPixmap(QPixmap())

        # delete all lines
        for l in self.lines:
            self.removeItem(l)
        self.lines = []

        self.selected_dot = None
        self.LScore.setHtml('0:0')

    def timerEvent(self, ev):
        self.game_update()

if __name__ == '__main__':
    App = QApplication(sys.argv)
    scene = DotsGame()
    sys.exit(App.exec_())
