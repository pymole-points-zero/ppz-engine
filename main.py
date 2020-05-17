# Using model weights engine generates game match and writes results to stdout.
import argparse
import json


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='mode', required=True)

parser_selfplay = subparsers.add_parser('selfplay', help='Run selfplay loop to generate example')
parser_selfplay.add_argument('--parameters', type=str, required=True)
parser_selfplay.add_argument('--weights', type=str, required=True)

parser_match = subparsers.add_parser('match', help='Match two neural networks')
parser_match.add_argument('--parameters', type=str, required=True)
parser_match.add_argument('--candidate_weights', type=str, required=True)
parser_match.add_argument('--best_weights', type=str, required=True)
parser_match.add_argument('--candidate_turns_first', action='store_true')

args = parser.parse_args()

test_params = {
    'field_size': (15, 15),
    'example_simulations': 2,
    'compare_simulations': 2,
    'random_crosses': False,
}

args.parameters = json.loads(args.parameters)
args.parameters.update(test_params)

if args.mode == 'selfplay':
    from selfplay import SelfplayLoop
    loop = SelfplayLoop(args)
    loop.run()

elif args.mode == 'match':
    from selfplay import MatchLoop
    loop = MatchLoop(args)
    loop.run()
