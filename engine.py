import math
import random
import numpy as np
from itertools import islice


class Game:
	sides = (
		(-1, 0),
		(0, -1),
		(0, 1),
		(1, 0)
	)

	diogonal = (
		(-1, -1),
		(1, 1),
		(-1, 1),
		(1, -1)
	)

	allsides = tuple(list(sides) + list(diogonal))

	def __init__(self, w=15, h=15):
		self.width = w
		self.height = h
		self.field_size = w * h

	def __str__(self):
		return '\n'.join(
			'\t'.join(str(item[0]) for item in row)
			for row in self.field
		)

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
		self.field = np.full((self.width, self.height, 2), fill_value=0, dtype=np.int8)
		self.turn = 1
		self.score = {-1: 0, 1: 0}
		self.sur_zones = []
		self.busy_dots = []
		self.free_dots = set(range(self.field_size))
		self.player = -1

		if random_crosses:
			cross = self._random_crosses()
		elif cross is None:
			cross = {}
		else:
			cross = self._make_1cross(center=True)

		for owner, dots in cross.items():
			for x, y in dots:
				self.put_dot(x, y, owner)
				self.fix_dot(self.get_ind_of_pos(x, y))

		return cross

	def put_dot(self, x, y, owner):
		self.field[x, y, 0] = owner

	def auto_turn(self, ind, owner=None):
		# Automatised method for player turn
		x, y = self.get_pos_of_ind(ind)
		if owner is None:
			owner = self.player
		self.put_dot(x, y, owner)
		self.fix_dot(ind)
		self.surround_check(mode='all')		# check all points of p1
		self.change_turn()					# change turn
		self.surround_check(mode='last')	# check p1 last turn for trapping 

	def fix_dot(self, dot_ind):
		self.busy_dots.append(dot_ind)
		self.free_dots.remove(dot_ind)

	def get_ind_of_pos(self, x, y):
		return self.width * y + x

	def get_pos_of_ind(self, ind):
		pos = (ind%self.width, ind//self.width)
		return pos

	def can_put_dot(self, x, y):
		# if no owner and not surrounded
		if self.field[x, y, 0] == 0 and self.field[x, y, 1] == 0:
			return True

		return False

	def neighbors_hor_ver(self, x, y):
		for off_x, off_y in self.sides:
			yield x+off_x, y+off_y

	def neighbors_all(self, x, y):
		for off_x, off_y in self.allsides:
			yield x+off_x, y+off_y

	def wave_check(self, start_x, start_y, visited):
		# self.player - surrounder
		# -self.player - surrounded
		chain = []
		
		toCheck = [(start_x, start_y)]
		checked = []

		while toCheck:
			cur_x, cur_y = toCheck.pop()

			visited[cur_y][cur_x] = True

			# волна достигла края игровой доски
			if self.field[cur_x, cur_y, 0] != self.player and \
				(cur_x == self.width - 1 or cur_x == 0 or cur_y == self.height - 1 or cur_y == 0):
				return (
					False,	# возвращаем пустую цепь
					set(checked) - set(chain)
				)

			checked.append((cur_x, cur_y))

			# инициализация соседних от текущей точки координат

			for neib_x, neib_y in self.neighbors_hor_ver(cur_x, cur_y):
				# проходимся только по непройденным соседям
				if visited[neib_y][neib_x]:
					continue

				visited[neib_y][neib_x] = True
				neib = (neib_x, neib_y)

				if self.field[neib_x, neib_y, 0] == self.player and self.field[neib_x, neib_y, 1] != -self.player:
					# добавляем точку в цепь, если она окружает
					chain.append(neib)
				else:
					# окружаемую точку или пустой пункт добавляем в стэк для дальнейшей проверки
					toCheck.append(neib)


		# создание графа, состоящего из точек цепи
		graph = {dot: [] for dot in chain}
		for i in range(len(chain) - 1):
			elm1 = chain[i]
			for elm2 in islice(chain, i + 1, len(chain)):
				if elm1 in self.neighbors_all(elm2[0], elm2[1]):
					graph[elm1].append(elm2)
					graph[elm2].append(elm1)

		# поиск циклов эйлера в графе
		start = 0
		pathes = []

		# для обработки следующей ситуации используется первый цикл while
		# #....#
		# .####.
		# .#...#
		# .####.
		# #....#

		while not pathes:
			while len(graph[chain[start]]) != 2:
				start += 1

			toCheck = [([chain[start]], 0)]

			while toCheck:
				cur_path, cur_path_len = toCheck.pop()
				last_element = cur_path[-1]

				for n in graph[last_element]:
					if n in cur_path:
						continue

					new_path = cur_path + [n]
					updated_path = (new_path, cur_path_len + self._points_distance(last_element, n))

					if chain[start] in graph[n] and len(new_path) >= 4:
						pathes.append(updated_path)
					else:
						toCheck.append(updated_path)

			start += 1

		# нахождение длиннейшего цикла эйлера
		longest_len = 0
		for path, length in pathes:
			if length > longest_len:
				chain = path

		return chain, set(checked) - set(chain)

	def surround_check(self, mode='all'):
		# формирование списка точек для проверки на окружение
		if mode == 'all':
			# итератор по всем точкам, которые нужно пройти
			to_check = (
				(x, y)
				for x in range(1, self.width - 1) for y in range(1, self.height - 1)
				if self.field[x, y, 0] == -self.player and self.field[x, y, 1] == 0
			)
		elif mode == 'last':
			to_check = [self.get_pos_of_ind(self.busy_dots[-1])]

		visited = [[False] * self.width for _ in range(self.height)]

		for x, y in to_check:
			if visited[y][x]:
				continue

			# запуск волны
			chain, sur = self.wave_check(x, y, visited)	# получаем цепь и окруженные точки

			# если волна не дошла до края и цепь не пуста
			if chain:
				for dot_x, dot_y in sur:
					# добавляем точку, если её еще нет в занятых
					if self.field[dot_x, dot_y, 0] == 0:
						d = self.get_ind_of_pos(dot_x, dot_y)
						if d not in self.busy_dots:
							self.fix_dot(d)

					# если точка принадлежит текущему игроку и она окружена, то она освобождается
					# от окружения путем убавления одного очка противоположного игрока
					if self.field[dot_x, dot_y, 0] == self.player and self.field[dot_x, dot_y, 1] == -self.player:
						self.score[-self.player] -= 1
					# если же точка вражеская, то получаем за неё плюс 1 к счету
					elif self.field[dot_x, dot_y, 0] == -self.player:
						self.score[self.player] += 1


					# меняем владельца точки на игрока, который завершил ход
					self.field[dot_x, dot_y, 1] = self.player

				if chain not in self.sur_zones:
					self.sur_zones.append(chain)

	def _random_crosses(self):
		variants = (
			(self._make_4crosses, None),
			(self._make_1cross, False),
			(self._make_1cross, True),
			(None, None)
		)

		func, *args = random.choice(variants)

		if func is None:
			return {-1: [], 1: []}
		elif args[0] is None:
			return func()
		else:
			return func(*args)

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
			crosses[-1].append(tuple(map(int, (x - 1, y - 1) )) )
			crosses[-1].append(tuple(map(int, (x, y) )) )
			crosses[1].append(tuple(map(int, (x, y - 1) )) )
			crosses[1].append(tuple(map(int, (x - 1, y) )) )

		return crosses

	def _make_1cross(self, center = False):
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

		crosses[-1].append(tuple(map(int, (x - 1, y - 1) )) )
		crosses[-1].append(tuple(map(int, (x, y) )) )
		crosses[1].append(tuple(map(int, (x, y - 1) )) )
		crosses[1].append(tuple(map(int, (x - 1, y) )) )

		return crosses

	def _points_distance(self, p1, p2):
		return math.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)

	def change_turn(self):
		# Определяем, кто ходит. Четный ход -1, нечетный 1
		self.turn += 1
		self.player = -self.player

	def is_ended(self):
		return not self.free_dots
