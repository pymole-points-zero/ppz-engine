from engine import Points
import random
import sys

def simple_surround():
    ##.#
    #.0.
    ##.#

    game = Points(3, 3)
    game.reset(random_crosses=False)

    game.auto_turn(0)
    game.auto_turn(1)
    game.auto_turn(2)
    game.auto_turn(3)
    game.auto_turn(4)
    game.auto_turn(5)
    game.auto_turn(6)
    game.auto_turn(7)

    print(game)
    print(game.score)


def one_point_multiple_surrounds():
    # #.#.#
    # .0.0.
    # #.#.#

    game = Points(5, 3)
    game.reset(random_crosses=False)

    game.make_move(1, 1)
    game.make_move(3, 1)
    game.make_move(5, 1)
    game.make_move(9, 1)
    game.make_move(11, 1)
    game.make_move(13, 1)

    game.make_move(6, -1)
    game.make_move(8, -1)

    game.make_move(7, 1)

    game.change_turn()
    print(game.player)
    game.surround_check(mode='surround')

    print(game)
    print(game.score)


def graph_while():
    # #....#
    # .#0##.
    # .#...#
    # .####.
    # #....#

    game = Points(6, 5)
    game.reset(random_crosses=False)
    print(game)

    game.make_move(1, 1)
    game.make_move(2, 1)
    game.make_move(3, 1)
    game.make_move(4, 1)
    game.make_move(6, 1)
    game.make_move(11, 1)
    game.make_move(12, 1)
    game.make_move(14, 1)
    game.make_move(15, 1)
    game.make_move(16, 1)
    game.make_move(18, 1)
    game.make_move(23, 1)
    game.make_move(25, 1)
    game.make_move(26, 1)
    game.make_move(27, 1)
    game.make_move(28, 1)

    game.make_move(8, -1)
    game.change_turn()
    game.surround_check(mode='suicide')

    print(game)
    print(game.score)


def random_moves_check():
    # TODO StopIteration error
    game = Points()
    game.reset(random_crosses=False)
    while not game.is_ended:
        try:
            temp = set(game.free_dots)
            a = random.choice(list(game.free_dots))
            print(a)
            game.auto_turn(a)
            print(game)
        except:
            import traceback
            traceback.print_exc()
            print(game)
            print(game.free_dots)
            print(a)
            print(game.get_pos_of_ind(a))
            print(game.moves[-1])
            print(game.get_pos_of_ind(game.moves[-1]))
            raise Exception


def house_test():
    game = Points(5, 5)
    game.reset(random_crosses=False)

    game.make_move_coordinate(2, 1, -1)
    game.make_move_coordinate(3, 2, -1)
    game.make_move_coordinate(2, 3, -1)
    game.make_move_coordinate(1, 2, -1)

    game.surround_check()

    print(game)
    print(game.field)


def suicide_test():
    game = Points(3, 3)

# TODO добавить тест на многократное переокружение зон
# TODO добавить тесты на домики
# TODO написать тесты на длину окружения

# random_moves_check()
# one_point_multiple_surrounds()
# simple_surround()
# graph_while()
house_test()