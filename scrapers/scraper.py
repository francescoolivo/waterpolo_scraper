import logging
import os.path
import re
from abc import ABC, abstractmethod
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm.contrib.logging import logging_redirect_tqdm
from unidecode import unidecode
from utils.constants import *
import yaml
from utils import utils
from queue import Queue
from writers.writer import Writer
logger = logging.getLogger('sdeng')

class Scraper(ABC):
	def __init__(self, writer: Writer):
		self.writer = writer
		self.franchises_cache = dict()
		self.teams_cache = dict()
		self.players_cache = dict()
		self.current_season = None
		self.current_game = None
		self.current_league = None
		self.current_edition = None
		return

	@abstractmethod
	def get_league(self):
		pass

	@abstractmethod
	def get_franchise(self, team_name):
		pass

	@abstractmethod
	def get_seasons(self, **kwargs):
		pass

	@abstractmethod
	def get_games(self, **kwargs):
		pass

	@abstractmethod
	def get_team_details(self, team_name: str):
		pass

	@abstractmethod
	def download_actions(self):
		pass

	def get_actions(self, **kwargs):
		actions = self.download_actions()

		return actions

	def get_player_url(self, player):
		return player['player_url']

	def download(self, **kwargs):
		league = self.get_league()
		logger.info(f'New league: {league["name"]}')
		self.current_league = league
		league_id = self.writer.check_and_insert_league(league)

		for season in self.get_seasons(**kwargs):
			season_id = self.writer.check_and_insert_season(season)
			season['season_id'] = season_id

			self.current_season = season

			edition = self.get_edition_details()
			edition['league_id'] = league_id
			edition['season_id'] = season_id
			edition_id = self.writer.check_and_insert_edition(edition)
			edition['edition_id'] = edition_id

			self.current_edition = edition

			games = self.get_games(**kwargs)

			with logging_redirect_tqdm():
				if kwargs['tg'] is True:
					from tqdm.contrib.telegram import tqdm
					iterator = tqdm(games, token=kwargs['tg_config']['token'], chat_id=kwargs['tg_config']['users'], desc=f'{self.current_league["name"]} {season["start"] % 100:02d}-{season["end"] % 100:02d}',
				                 position=0, leave=True)
				else:
					from tqdm import tqdm
					iterator = tqdm(games,
				                 desc=f'{self.current_league["name"]} {season["start"] % 100:02d}-{season["end"] % 100:02d}',
				                 position=0, leave=True)
				for game in iterator:
					for team_name in [game['home_team'], game['away_team']]:
						team_str = f'{season["start"]}-{season["end"]}:{team_name}'

						if team_str not in self.franchises_cache:
							franchise = self.get_franchise(team_name)
							franchise_id = self.writer.check_and_insert_franchise(franchise)
							self.franchises_cache[team_str] = franchise_id
						else:
							franchise_id = self.franchises_cache[team_str]

						if team_str not in self.teams_cache:
							team = self.get_team_details(team_name)
							team['franchise_id'] = franchise_id

							team_id = self.writer.check_and_insert_team(team)
							self.teams_cache[team_str] = team_id
							edition_participant = {
								'team_id': team_id,
								'edition_id': edition_id,
								'team': team_name,
							}
							if 'conference' in team:
								edition_participant['conference'] = team['conference']
							else:
								edition_participant['conference'] = None

							self.writer.check_and_insert_edition_participant(edition_participant)
						else:
							team_id = self.teams_cache[team_str]

						if team_name == game['home_team']:
							game['home_team_id'] = team_id
						elif team_name == game['away_team']:
							game['away_team_id'] = team_id

					game['season_id'] = season_id
					game['edition_id'] = edition_id
					game_id = self.writer.check_and_insert_game(game)
					game['game_id'] = game_id
					logger.info(f'New game: {game["home_team"]}-{game["away_team"]} of {game["date"]}')

					self.current_game = game

					if game['status'] in (PLAYED, LIVE):
						actions = self.download_actions()
						actions = self.clean_actions(actions)

						self.writer.check_and_insert_actions(actions)

	# def add_period_start_and_end(self, raw_actions, period_duration=600, periods=4, elam_ending=False):
	# 	actions = []
	#
	# 	max_period = raw_actions[-1]['period']
	#
	# 	period = 1
	# 	home_score = 0
	# 	away_score = 0
	#
	# 	actions.append({
	# 		'action_id': f'GS-{period}',
	# 		'description': GAME_START,
	# 		'team': None,
	# 		'home_score': home_score,
	# 		'away_score': away_score,
	# 		'remaining_period_time': period_duration,
	# 		'player': None,
	# 		'flags': [],
	# 		'x': None,
	# 		'y': None,
	# 		'period': 1,
	# 	})
	#
	# 	actions.append({
	# 		'action_id': f'PS-{period}',
	# 		'description': PERIOD_START,
	# 		'team': None,
	# 		'home_score': home_score,
	# 		'away_score': away_score,
	# 		'remaining_period_time': period_duration,
	# 		'player': None,
	# 		'flags': [],
	# 		'x': None,
	# 		'y': None,
	# 		'period': 1,
	# 	})
	#
	# 	for raw_action in raw_actions:
	# 		if raw_action['period'] and raw_action['period'] != period:
	# 			remaining_period_time = period_duration if raw_action['period'] <= periods else 300
	# 			actions.append({
	# 				'action_id': f'PE-{period}',
	# 				'description': PERIOD_END,
	# 				'team': None,
	# 				'home_score': home_score,
	# 				'away_score': away_score,
	# 				'remaining_period_time': 0,
	# 				'player': None,
	# 				'flags': [],
	# 				'x': None,
	# 				'y': None,
	# 				'period': period,
	# 			})
	#
	# 			period = raw_action['period']
	#
	# 			if elam_ending and period == max_period:
	# 				remaining_period_time = raw_action['remaining_period_time']
	#
	# 			actions.append({
	# 				'action_id': f'PS-{period}',
	# 				'description': PERIOD_START,
	# 				'team': None,
	# 				'home_score': home_score,
	# 				'away_score': away_score,
	# 				'remaining_period_time': remaining_period_time,
	# 				'player': None,
	# 				'flags': [],
	# 				'x': None,
	# 				'y': None,
	# 				'period': period,
	# 			})
	#
	# 		home_score = raw_action['home_score']
	# 		away_score = raw_action['away_score']
	#
	# 		actions.append(raw_action)
	#
	# 	actions.append({
	# 		'action_id': f'PE-{period}',
	# 		'description': PERIOD_END,
	# 		'team': None,
	# 		'home_score': home_score,
	# 		'away_score': away_score,
	# 		'remaining_period_time': 0,
	# 		'player': None,
	# 		'flags': [],
	# 		'x': None,
	# 		'y': None,
	# 		'period': period,
	# 	})
	#
	# 	actions.append({
	# 		'action_id': f'GE-{period}',
	# 		'description': GAME_END,
	# 		'team': None,
	# 		'home_score': home_score,
	# 		'away_score': away_score,
	# 		'remaining_period_time': 0,
	# 		'player': None,
	# 		'flags': [],
	# 		'x': None,
	# 		'y': None,
	# 		'period': period,
	# 	})
	#
	# 	return actions

	def get_edition_details(self):
		# TODO: set values
		edition = {
			'league_id': None,
			'season_id': None,
			'number_of_teams': None,
			'number_of_periods': 4,
			'period_duration': 600,
			'shot_clock_duration': 24,
			'overtime_duration': 300
		}

		return edition

	def clean_name(self, name):
		if name is None:
			return None

		def uppercase_nth_char(string, index):
			return string[:index] + string[index].upper() + string[index + 1:]

		name = unidecode(name)

		# remove punctuation marks
		for char in ('.', ','):
			name = name.replace(char, '')

		# replace apostrophes
		for char in ('"', '’', "''"):
			name = name.replace(char, "'")

		new_name_split = list()

		for split_temp in name.split():
			split_temp = split_temp.title()

			if split_temp.startswith('Mc') and len(split_temp) > 2:
				split_temp = uppercase_nth_char(split_temp, 2)

			if split_temp in ('Ii', 'Iii', 'Iv'):
				split_temp = split_temp.upper()

			new_name_split.append(split_temp)

		name = ' '.join(new_name_split)

		for string_to_remove in (' III', ' II', ' IV', ' Jr', ' Sr'):
			name = name.replace(string_to_remove, '').strip()

		return name

	def get_debug_url(self):
		if 'pbp_url' in self.current_game:
			return self.current_game['pbp_url']
		else:
			return self.current_game['website_id']

	def clean_actions(self, raw_actions):
		# TODO: insert player logic (previous from get_game_data)

		action_number = 1
		actions = []

		game = self.current_game

		pending_actions = dict()

		for raw_action in raw_actions:
			action = {
				'season_id': self.current_edition['season_id'],
				'edition_id': self.current_edition['edition_id'],
				'game_id': game['game_id'],
				'action_number': None,
				'period': None,
				'home_score': None,
				'away_score': None,
				'remaining_period_time': None,
				'type': None,
				'player_id': None,
				'team_id': None,
				'opponent_id': None,
				'x': None,
				'y': None,
				'target_x': None,
				'target_y': None,
				'details': None,
				'linked_action_number': None
			}

			main_type_code = raw_action['description']
			if main_type_code is None:
				continue
			period = raw_action['period']
			# home_score = raw_action['home_score']
			# away_score = raw_action['away_score']
			remaining_period_time = raw_action['remaining_period_time']

			team_id = None
			team_loc = None

			if raw_action['team'] is not None:
				team_name = raw_action['team']

				if team_name.title() == game['home_team'].title():
					team_id = game['home_team_id']
					team_loc = 'home_players'
				elif team_name.title() == game['away_team'].title():
					team_id = game['away_team_id']
					team_loc = 'away_players'
				else:
					team_id = None

			player = raw_action['player']

			if player is not None and team_id is not None:
				player_str = f'{team_id} {player}'

				if player_str not in self.players_cache:
					player_id_website = raw_action['player_id']

					player, contract = self.current_season['players'][player_id_website]

					contract['season_id'] = self.current_season['season_id']
					contract['team_id'] = team_id

					if 'full_name' not in player:
						logger.error(f'Missing player\'s full name!\nPlayer is {player}')
						exit(0)

					player_id = self.writer.insert_player_and_contract(player, contract)
					self.players_cache[player_str] = player_id
				else:
					player_id = self.players_cache[player_str]
			else:
				player_id = None

			x = raw_action['x']
			y = raw_action['y']

			if 'target_x' not in raw_action:
				target_x = None
				target_y = None
			else:
				target_x = raw_action['target_x']
				target_y = raw_action['target_y']

			linked_action_number = None

			# action details
			flags = set(raw_action['flags'])
			details = ':'.join(flags)

			home_score = raw_action['home_score']
			away_score = raw_action['away_score']

			# types whose last possible linked action has been found, and therefore can be removed. We cannot remove them on the go since this would change the collection that we are iterating
			general_types_to_remove = []
			# a pending general type is an action which may be referenced by another action, and therefore we use this dict to track the id of the action to link
			for pending_general_type in pending_actions:
				# save link
				if main_type_code in utils.get_referenced_types(pending_general_type):
					linked_action_number = pending_actions[pending_general_type]

				# this code must be ignored so we skip it. It's the case of substitutions between a foul and the free throws
				if main_type_code in utils.get_ignored_types(pending_general_type):
					continue

				# last possible action, so we "close" it by removing it from the dict
				if main_type_code in utils.get_closing_types(pending_general_type):
					general_types_to_remove.append(pending_general_type)

				# if we did not reference, nor ignore nor close an action it means that something that we imagined could have happened did not happen. Therefore, we remove it.
				# Before removing it, we check if we are in the peculiar cases in which a team rebound or a team steal happened, since these are not tracked.
				if main_type_code not in utils.get_referenced_types(
						pending_general_type) and main_type_code not in utils.get_closing_types(pending_general_type):

					general_types_to_remove.append(pending_general_type)

			for general_type_to_remove in general_types_to_remove:
				pending_actions.pop(general_type_to_remove)

			if team_id == self.current_game['away_team_id']:
				opponent_team_id = self.current_game['home_team_id']
			elif team_id == self.current_game['home_team_id']:
				opponent_team_id = self.current_game['away_team_id']
			else:
				opponent_team_id = None

			action['action_number'] = action_number
			action['period'] = period
			action['home_score'] = home_score
			action['away_score'] = away_score
			action['remaining_period_time'] = remaining_period_time
			action['type'] = main_type_code
			action['player_id'] = player_id
			action['team_id'] = team_id
			action['opponent_id'] = opponent_team_id
			action['x'] = x
			action['y'] = y
			action['target_x'] = target_x
			action['target_y'] = target_y
			action['details'] = details
			action['linked_action_number'] = linked_action_number

			actions.append(action)

			action_general_type = utils.get_general_type(main_type_code, flags)
			if action_general_type:
				pending_actions[action_general_type] = action_number

			action_number += 1

		return actions
