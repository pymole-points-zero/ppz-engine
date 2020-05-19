# Using model weights engine generates game match and writes results to stdout.
import argparse
import json


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='mode', required=True)

parser_selfplay = subparsers.add_parser('loops', help='Run loops loop to generate example')
parser_selfplay.add_argument('--parameters', type=str, required=True)
parser_selfplay.add_argument('--weights', type=str, required=True)

parser_match = subparsers.add_parser('match', help='Match two neural networks')
parser_match.add_argument('--parameters', type=str, required=True)
parser_match.add_argument('--candidate_weights', type=str, required=True)
parser_match.add_argument('--best_weights', type=str, required=True)
parser_match.add_argument('--candidate_turns_first', action='store_true')

parser_protocol = subparsers.add_parser('pointsaiprotocol', help='Run PointsAIProtocol6 mode')
parser_protocol.add_argument('--parameters', type=str, required=True)
parser_protocol.add_argument('--weights', type=str, required=True)
parser_protocol.add_argument('--pipe', type=str, required=True)

args = parser.parse_args()


if args.mode == 'loops':
    test_params = {
        'field_size': (15, 15),
        'example_simulations': 2,
        'compare_simulations': 2,
        'random_crosses': False,
    }

    args.parameters = json.loads(args.parameters)
    args.parameters.update(test_params)

    from loops import SelfplayLoop
    loop = SelfplayLoop(args)
    loop.run()

elif args.mode == 'match':
    test_params = {
        'field_size': (15, 15),
        'example_simulations': 2,
        'compare_simulations': 2,
        'random_crosses': False,
    }
    args.parameters = json.loads(args.parameters)
    args.parameters.update(test_params)

    from loops import MatchLoop
    loop = MatchLoop(args)
    loop.run()

elif args.mode == 'pointsaiprotocol':
    from loops import PAIPLoop

    loop = PAIPLoop(args)
    loop.run()