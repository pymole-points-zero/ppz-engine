from engine import Game
import sgf
import os
import numpy as np
from logic import *
import pickle

def get_position_of_string(s):
	return (turn_coder[s[0]], turn_coder[s[1]])

def get_batches(batch_size, sgf_dir):
	files = os.listdir(sgf_dir)
	i = 0
	while i < len(files):
		len_limit = min(batch_size, len(files) - i)
		batch = []
		for file_name in files[i : i + len_limit]:
			with open(sgf_dir + file_name, 'r') as f:
				batch.append( sgf.parse(f.read()) )
		i += len_limit
		yield batch

# settings
batch_size = 10		# n games will be packed inside one file
# sgf_dir = 'C:/Users/Roman/Downloads/data/'
sgf_dir = 'C:/Users/Roman/Downloads/test_sgf/'
examples_dir = 'scraping/examples/'
turn_coder = { c: n for n, c in enumerate('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNO')}

game = Game(39, 32)

batch_generator = get_batches(batch_size, sgf_dir)

# for each batch generate file of examples
for batch_ind, batch in enumerate(batch_generator):
	batch_examples = []

	for sgf_game_ind, sgf_game in enumerate(batch):
		cur_game_examples = []
		tree = sgf_game.children[0]
		settings_node, *turns_nodes = tree.nodes
		
		game.reset(
			cross = {
				-1: (get_position_of_string(dot) for dot in settings_node.properties['AB']),
				1: (get_position_of_string(dot) for dot in settings_node.properties['AW'])
			}
		)
		
		player_color = None
		for turn_ind, turn_node in enumerate(turns_nodes):
			new_player_color = 'B' if 'B' in turn_node.properties else 'W'

			# detect grounding or additional turn
			if player_color == new_player_color:
				break

			player_color = new_player_color
			if len(turn_node.properties[player_color]) > 1:
				break

			# get turn record
			turn = turn_node.properties[player_color][0]

			# first 2 symbols is turn of player
			if len(turn) > 2:
				turn = turn[:2]

			pos = get_position_of_string(turn)
			pos_ind = game.get_ind_of_pos(*pos)

			# possibility of each action
			pi = [0 for _ in range(game.field_size)]
			pi[pos_ind] = 1

			# multiply examples by rotating them
			pi = np.reshape(np.array(pi), (game.height, game.width))
			curPlrPercField = getFieldPerc(game.field, game.player)			# get field from player's percpective

			v_flip_perc = np.flip(curPlrPercField, 0)
			v_flip_pi = np.flip(pi, 0)
			cur_game_examples.extend([
				[curPlrPercField, 				np.reshape(pi, (game.field_size,)), 					None],
				[np.flip(curPlrPercField, 1), 	np.reshape(np.flip(pi, 1), (game.field_size,)),			None],
				[v_flip_perc, 					np.reshape(v_flip_pi, (game.field_size,)), 				None],
				[np.flip(v_flip_perc, 1), 		np.reshape(np.flip(v_flip_pi, 1), (game.field_size,)), 	None]
			])
			try:
				game.auto_turn(pos_ind)
			except:
				print("Batch", batch_ind)
				print("Game inside batch ", sgf_game_ind)
				print(game)
				print(pos)
				print(turn)
				print(turn_ind)
				input()

		result = settings_node.properties['RE'][0][0]
		v = -1 if result == 'B' else 1 if result == 'W' else 0
		v *= -game.player
		print(v)

		# insert game reward to examples
		# for the last turned player (reward = v) for another (reward = -v)
		for g in range(len(cur_game_examples) - 1, 2, -4):
			for e in range(4):
				cur_game_examples[g-e][2] = v
			v = -v

		batch_examples += cur_game_examples

	with open(examples_dir + "batch" + str(batch_ind) + ".txt", 'wb') as file:
		pickle.dump(batch_examples, file)




		





