from engine import Game


def simple_surround():
    ##.#
    #.0.
    ##.#

    game = Game(3, 3)
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


def double_simple():
    # #.##.#
    # .0..0.
    # #.##.#

    game = Game(6, 3)
    game.reset(random_crosses=False)

    game.put_dot(1, 0, 1)
    game.put_dot(2, 1, 1)
    game.put_dot(1, 2, 1)
    game.put_dot(0, 1, 1)

    game.put_dot(1, 1, -1)

    game.put_dot(4, 0, 1)
    game.put_dot(5, 1, 1)
    game.put_dot(4, 2, 1)
    game.put_dot(3, 1, 1)

    game.put_dot(4, 1, -1)


    game.change_turn()
    game.surround_check(mode='all')

    print(game)
    print(game.score)


def graph_while():
    # #....#
    # .#0##.
    # .#...#
    # .####.
    # #....#

    game = Game(5, 5)
    game.reset(random_crosses=False)
    print(game)

    game.put_dot(1, 0, 1)
    game.put_dot(2, 0, 1)
    game.put_dot(3, 0, 1)
    game.put_dot(0, 1, 1)
    game.put_dot(4, 1, 1)
    game.put_dot(0, 2, 1)
    game.put_dot(2, 2, 1)
    game.put_dot(3, 2, 1)
    game.put_dot(0, 3, 1)
    game.put_dot(4, 3, 1)
    game.put_dot(1, 4, 1)
    game.put_dot(2, 4, 1)
    game.put_dot(3, 4, 1)


    game.put_dot(1, 1, -1)
    game.fix_dot(6)
    game.change_turn()
    game.surround_check(mode='last')

    print(game)
    print(game.score)


double_simple()
simple_surround()
graph_while()