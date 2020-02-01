from points import Points
import unittest
import random


class PointsTest(unittest.TestCase):
    def setUp(self):
        self.game = Points(15, 15)
        self.game.reset(random_crosses=False)

    def test_empty_house(self):
        #####
        ##.##
        #.#.#
        ##.##
        #####

        self.game.make_move_coordinate(2, 1, -1)
        self.game.make_move_coordinate(3, 2, -1)
        self.game.make_move_coordinate(2, 3, -1)
        self.game.make_move_coordinate(1, 2, -1)

        self.game.surround_check()

        self.assertEqual(self.game.field[2, 2, 1], 0, 'House is not empty')

    def test_suicide(self):
        #####
        ##.##
        #.X.#
        ##.##
        #####

        self.game.make_move_coordinate(2, 1, -1)
        self.game.make_move_coordinate(1, 2, -1)
        self.game.make_move_coordinate(3, 2, -1)
        self.game.make_move_coordinate(2, 3, -1)

        self.game.make_move_coordinate(2, 2, 1)

        self.game.surround_check(mode='suicide')

        self.assertEqual(self.game.field[2, 2, 1], -1, 'Suicide point is not surrounded.')
        self.assertEqual(self.game.score[-1], 1, 'Wrong score.')

    def test_one_point_multiple_surrounds(self):
        """
        #####
        #.#.#
        .0.0.
        #.#.#
        #####
        """

        self.game.make_move_coordinate(1, 1, -1)
        self.game.make_move_coordinate(3, 1, -1)

        self.game.make_move_coordinate(0, 2, -1)
        self.game.make_move_coordinate(1, 2, 1)
        self.game.make_move_coordinate(3, 2, 1)
        self.game.make_move_coordinate(4, 2, -1)

        self.game.make_move_coordinate(1, 3, -1)
        self.game.make_move_coordinate(3, 3, -1)

        self.game.make_move_coordinate(2, 2, -1)

        self.game.surround_check()

        self.assertEqual(self.game.field[1, 2, 1], -1, 'First point is not surrounded.')
        self.assertEqual(self.game.field[3, 2, 1], -1, 'Second point is not surrounded.')

        self.assertEqual(self.game.score[-1], 2, 'Wrong score.')
        self.assertEqual(self.game.score[1], 0, 'Wrong score.')

    def test_graph_while(self):
        """
        .OOOO.
        O.X..O
        O.OOO.
        O....O
        .OOOO.
        """

        self.game.make_move_coordinate(1, 0, -1)
        self.game.make_move_coordinate(2, 0, -1)
        self.game.make_move_coordinate(3, 0, -1)
        self.game.make_move_coordinate(4, 0, -1)

        self.game.make_move_coordinate(0, 1, -1)
        self.game.make_move_coordinate(2, 1, 1)
        self.game.make_move_coordinate(5, 1, -1)

        self.game.make_move_coordinate(0, 2, -1)
        self.game.make_move_coordinate(2, 2, -1)
        self.game.make_move_coordinate(3, 2, -1)
        self.game.make_move_coordinate(4, 2, -1)

        self.game.make_move_coordinate(0, 3, -1)
        self.game.make_move_coordinate(5, 3, -1)

        self.game.make_move_coordinate(1, 4, -1)
        self.game.make_move_coordinate(2, 4, -1)
        self.game.make_move_coordinate(3, 4, -1)
        self.game.make_move_coordinate(4, 4, -1)

        self.game.surround_check()

    def test_shortest_chain(self):
        """
        .O...
        O.O..
        O.OO.
        OX..O
        .OOO.
        """

        self.game.make_move_coordinate(1, 0, -1)

        self.game.make_move_coordinate(0, 1, -1)
        self.game.make_move_coordinate(2, 1, -1)

        self.game.make_move_coordinate(0, 2, -1)
        self.game.make_move_coordinate(2, 2, -1)
        self.game.make_move_coordinate(3, 2, -1)

        self.game.make_move_coordinate(0, 3, -1)
        self.game.make_move_coordinate(1, 3, 1)
        self.game.make_move_coordinate(4, 3, -1)

        self.game.make_move_coordinate(1, 4, -1)
        self.game.make_move_coordinate(2, 4, -1)
        self.game.make_move_coordinate(3, 4, -1)

        self.game.surround_check()

        self.assertNotEqual(self.game.field[2, 2, 1], -1, 'Wrong chain.')

    def test_simple_surround(self):
        """
        .0.
        OXO
        .O.
        """
        self.game.make_move_coordinate(1, 0, -1)

        self.game.make_move_coordinate(0, 1, -1)
        self.game.make_move_coordinate(1, 1, 1)
        self.game.make_move_coordinate(2, 1, -1)

        self.game.make_move_coordinate(1, 2, -1)

        self.game.surround_check()

        self.assertEqual(self.game.field[1, 1, 1], -1, 'Point is not surrounded.')
        self.assertEqual(self.game.score[-1], 1, 'Wrong score.')

    def test_random_moves(self):
        while not self.game.is_ended:
            a = random.choice(list(self.game.free_dots))
            self.game.auto_turn(a)
