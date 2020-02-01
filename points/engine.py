import math
import random
import numpy as np
from itertools import islice
from functools import partial


class Points:
	sides = (
		(-1, 0),
		(0, -1),
		(0, 1),
		(1, 0)
	)

	diagonal = (
		(-1, -1),
		(1, 1),
		(-1, 1),
		(1, -1)
	)

	allsides = tuple(list(sides) + list(diagonal))

	def __init__(self, w=15, h=15):
		self.width = w
		self.height = h
		self.field_size = w * h

	def __str__(self):
		return '\n'.join(
			'\t'.join(str(item[0]) for item in row)
			for row in self.field
		) + '\n'

	'''
	каждая точка (x, y) характеризуется:
		её обладателем [0]:
			0 - ничья
			-1 - принадлежит первому игроку
			1 - принадлежит второму игроку
		окруженностью [1]:
			0 - никем не окружена
			-1 - окружена первым игроком
			1 - окружена вторым игроком
	'''

	def reset(self, random_crosses=True, cross=None):
		self.field = np.zeros((self.width, self.height, 2), dtype=np.int8)
		self.turn = 1
		self.score = {-1: 0, 1: 0}
		# self.sur_zones = []
		self.moves = []
		self.free_dots = set(range(self.field_size))
		self.player = -1

		if random_crosses:
			cross = self._random_crosses()
		elif cross is None:
			cross = {-1: [], 1: []}
		else:
			cross = self._make_1cross(center=True)

		for owner, dots in cross.items():
			for x, y in dots:
				self.make_move(self.get_ind_of_pos(x, y), owner)

		self.starting_crosses = cross

	def change_owner(self, x, y, owner):
		self.field[x, y, 0] = owner

	def make_move(self, ind, owner):
		self.change_owner(*self.get_pos_of_ind(ind), owner)

		self.moves.append(ind)
		self.free_dots.remove(ind)

	def make_move_coordinate(self, x, y, owner):
		self.change_owner(x, y, owner)
		ind = self.get_ind_of_pos(x, y)
		self.moves.append(ind)
		self.free_dots.remove(ind)

	def auto_turn(self, ind):
		# Automatised method for player turn
		self.make_move(ind, self.player)

		self.surround_check(mode='surround')		# check surrounds
		self.change_turn()
		self.surround_check(mode='suicide')			# check suicide move into house

	def get_ind_of_pos(self, x, y):
		return self.width * y + x

	def get_pos_of_ind(self, ind):
		return ind%self.width, ind//self.width

	def can_put_dot(self, x, y):
		# if no owner and not surrounded
		return self.field[x, y, 0] == 0 and self.field[x, y, 1] == 0

	def neighbors_hor_ver(self, x, y):
		for off_x, off_y in self.sides:
			yield x+off_x, y+off_y

	def neighbors_all(self, x, y):
		for off_x, off_y in self.allsides:
			yield x+off_x, y+off_y

	def is_edge(self, x, y):
		return x == self.width - 1 or x == 0 or y == self.height - 1 or y == 0

	def is_on_board(self, x, y):
		return 0 <= x <= self.width - 1 and 0 <= y <= self.height - 1

	def chain_check(self, start_x, start_y, visited):
		# self.player - the surrounding
		# -self.player - surrounded

		# исключаем поиски цепи, которые начинаются с точки, принадлежащей окружающему, а не окружаемому
		if self.field[start_x, start_y, 0] == self.player:
			return None, None

		surrounding_dots = set()
		
		to_check = {(start_x, start_y)}
		checked = set()

		# флаг, который изменяется на True, если в внутри окружения обнаружатся точки окружаемого
		surrounded_inside = self.field[start_x, start_y, 0] == -self.player

		while to_check:
			cur_dot = to_check.pop()
			cur_x, cur_y = cur_dot

			# print('cur_dot', cur_dot)

			checked.add(cur_dot)

			for neib_x, neib_y in self.neighbors_hor_ver(cur_x, cur_y):
				neib = (neib_x, neib_y)

				if self.field[neib_x, neib_y, 0] == self.player and self.field[neib_x, neib_y, 1] != -self.player:
					# добавляем точку в цепь, если она окружает
					surrounding_dots.add(neib)

				elif neib in visited or self.field[neib_x, neib_y, 0] != self.player and self.is_edge(neib_x, neib_y):
					# наткнулись на соседа текущей точки, который уже доходил до края или же
					# непосредстенно текущая точка достигла достигла края игровой доски
					sur = checked - surrounding_dots
					visited.update(sur)

					# возвращаем пустую цепь
					# print('empty', neib in visited, neib)
					return None, None

				elif neib not in checked:
					# окружаемую точку или пустой пункт добавляем в стэк для дальнейшей проверки
					to_check.add(neib)
					if self.field[neib_x, neib_y, 0] == -self.player:
						surrounded_inside = True

		# если внутри нет окруженных точек, но есть замкнутая цепь, значит мы встретили "домик"
		if not surrounded_inside:
			return None, None

		print('surrounding dots', surrounding_dots)

		# создание графа, состоящего из точек цепи
		graph = {dot: [] for dot in surrounding_dots}
		for i, dot1 in enumerate(surrounding_dots):
			for dot2 in islice(surrounding_dots, i + 1, len(surrounding_dots)):
				if dot1 in self.neighbors_all(*dot2):
					graph[dot1].append(dot2)
					graph[dot2].append(dot1)

		# ищем самую длиннейшую замыкающую цепь (цикл Эйлера)
		sur_iter = iter(surrounding_dots)
		start = next(sur_iter)
		surround_variations = []

		# для обработки следующей ситуации используется первый цикл while
		# #....#
		# .####.
		# .#...#
		# .####.
		# #....#

		while not surround_variations:
			while len(graph[start]) != 2:
				start = next(sur_iter)

			to_check = [[start]]

			while to_check:
				cur_path = to_check.pop()
				last_element = cur_path[-1]

				for neigh_element in graph[last_element]:
					if neigh_element in cur_path:
						continue

					new_path = cur_path + [neigh_element]

					if start in graph[neigh_element] and len(new_path) >= 4:
						surround_variations.append(new_path)
					else:
						to_check.append(new_path)

			start = next(sur_iter)

		# нахождение длиннейшего цикла эйлера
		chain = max(surround_variations, key=len)

		return chain, checked - set(chain)

	def surround_check(self, mode='surround'):
		# формирование списка точек для проверки на окружение
		if mode == 'surround':
			# итератор по всем точкам, которые нужно пройти
			# нужно пройти только 4 соседние точки от последней поставленной, чтобы определить
			# что именно она могла окружить
			to_check = (
				(x, y)
				for x, y in self.neighbors_hor_ver(*self.get_pos_of_ind(self.moves[-1]))
				if self.is_on_board(x, y) and not self.is_edge(x, y)
			)
		elif mode == 'suicide':
			pos = self.get_pos_of_ind(self.moves[-1])
			if self.is_edge(*pos):
				return

			to_check = (pos,)

		visited = set()

		for check_dot in to_check:
			if check_dot in visited:
				continue

			x, y = check_dot

			# print(check_dot)

			# ищем область окружения точки, если она есть
			chain, sur = self.chain_check(x, y, visited)	# получаем цепь и окруженные точки

			# print(chain, sur)

			# если волна не дошла до края и цепь не пуста
			if chain:
				for dot in sur:
					dot_x, dot_y = dot
					# добавляем точку, если её еще нет в занятых
					self.free_dots.discard(self.get_ind_of_pos(*dot))

					# если точка принадлежит текущему игроку и она окружена, то она освобождается
					# от окружения путем убавления одного очка противоположного игрока
					if self.field[dot_x, dot_y, 0] == self.player and self.field[dot_x, dot_y, 1] == -self.player:
						self.score[-self.player] -= 1
					# если же точка вражеская, то получаем за неё плюс 1 к счету
					elif self.field[dot_x, dot_y, 0] == -self.player:
						self.score[self.player] += 1

					# меняем владельца точки на игрока, который завершил ход
					self.field[dot_x, dot_y, 1] = self.player

				# if chain not in self.sur_zones:
				# 	self.sur_zones.append(chain)

	def _random_crosses(self):
		crosses_func = random.choice(self.cross_functions)
		return crosses_func()

	def _make_4crosses(self):
		min_side = min(self.width, self. height)

		# square where the crosses will be
		square_side_len = math.floor(self._points_distance((min_side//2, 0), (0, min_side//2)))

		rand_cross_center = lambda: (
			math.floor(random.uniform(0.3, 0.6) * square_side_len),
			random.choice([-1, 1]) * math.floor(random.uniform(0.3, 0.6) * square_side_len)
		)

		# get two crosses relativly to the center of the board
		cross1_center = rand_cross_center()

		while True:
			cross2_center = rand_cross_center()
			if self._points_distance(cross1_center, cross2_center) > 4:
				break

		crosses_centers = [
			cross1_center,
			cross2_center
		]

		# reflect by horizontal and vertical side
		vertical_reflection = random.choice([-1, 1])
		for x, y in list(crosses_centers):
			crosses_centers.append( (-x, vertical_reflection * y) )

		# make absolute coords
		board_centerW, board_centerH = self.width//2, self.height//2
		for i in range(len(crosses_centers)):
			c = crosses_centers[i]
			crosses_centers[i] = (c[0] + board_centerW, c[1] + board_centerH)

		# make crosses
		crosses = {
			-1: [],
			1: []
		}

		for x, y in crosses_centers:
			crosses[-1].append((int(x - 1), int(y - 1)))
			crosses[-1].append((int(x), int(y)))
			crosses[1].append((int(x), int(y - 1)))
			crosses[1].append((int(x - 1), int(y)))

		return crosses

	def _make_1cross(self, center=False):
		# center

		crosses = {
			-1: [],
			1: []
		}

		if center:
			x, y = self.width//2, self.height//2
		else:
			# randomize the position of the cross
			x = random.randint(1, self.width - 2)
			y = random.randint(1, self.height - 2)

		crosses[-1].append((int(x - 1), int(y - 1)))
		crosses[-1].append((int(x), int(y)))
		crosses[1].append((int(x), int(y - 1)))
		crosses[1].append((int(x - 1), int(y)))

		return crosses

	@staticmethod
	def _points_distance(p1, p2):
		return math.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)

	def change_turn(self):
		# Смена хода
		self.turn += 1
		self.player = -self.player

	def get_state(self):
		return ' '.join(map(str, self.moves))

	@property
	def field_shape(self):
		return self.width, self.height

	@property
	def is_ended(self):
		return not self.free_dots

	def get_winner(self):
		if self.score[-1] > self.score[1]:
			return -1
		if self.score[1] > self.score[-1]:
			return 1

		return 0

	cross_functions = (
		partial(_make_1cross, False),
		partial(_make_1cross, True),
		_make_4crosses,
		lambda: {-1:[], 1:[]}
	)