import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from unidecode import unidecode
from utils import utils
from utils.constants import *
import pandas as pd
from writers.writer import Writer
from selenium.common.exceptions import SessionNotCreatedException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.firefox.service import Service
import re
from seleniumwire import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import requests
from scrapers.scraper import Scraper as AbstractScraper
logger = logging.getLogger('waterpolo')

headers = {
	'Host': 'arena.total-waterpolo.com',
	'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0',
	'Accept': '*/*',
	'Accept-Language': 'en-US,en;q=0.5',
	'Accept-Encoding': 'gzip, deflate, br',
	'Access-Control-Request-Method': 'GET',
	'Access-Control-Request-Headers': 'authorization,content-type',
	'Referer': 'https://total-waterpolo.com/',
	'Origin': 'https://total-waterpolo.com',
	'Connection': 'keep-alive',
	'Sec-Fetch-Dest': 'empty',
	'Sec-Fetch-Mode': 'cors',
	'Sec-Fetch-Site': 'same-site',
}


class Scraper(AbstractScraper, ABC):

	def __init__(self, writer: Writer, season_mapping):
		super().__init__(writer)
		self.season_mapping = season_mapping
		self.authorization = ''

		url = 'https://total-waterpolo.com/tw_match/4432'
		exe = GeckoDriverManager().install()
		options = Options()
		options.add_argument('-headless')  # os.environ['WDM_LOG'] = str(logging.NOTSET)
		try:
			driver = webdriver.Firefox(service=Service(exe), options=options)
		except SessionNotCreatedException:
			exe = GeckoDriverManager(version="v0.31.0").install()
			driver = webdriver.Firefox(service=Service(exe), options=options)

		while self.authorization == '':
			driver.get(url)

			for request in driver.requests:
				# print(request.headers.keys())
				if 'Authorization' in request.headers:
					self.authorization = request.headers['Authorization']
					break
		driver.quit()

		# print('AUTH:', self.authorization)

		headers['Authorization'] = self.authorization

	def get_seasons(self, **kwargs):
		first_year = 2022
		last_starting_year = datetime.now().year if datetime.now().month >= 9 else datetime.now().year - 1

		seasons = []

		for year in range(first_year, last_starting_year + 1):
			if year not in self.season_mapping:
				continue

			season = {
				'start': year,
				'end': year + 1,
				'code': self.season_mapping[year],
			}

			season_code = f'{season["start"]}-{season["end"]}'

			if 'seasons' in kwargs and kwargs['seasons'] and season_code not in kwargs['seasons']:
				continue

			season['players'] = dict()
			season['teams'] = dict()
			seasons.append(season)

		return seasons

	def get_games(self, **kwargs):
		url = f'https://arena.total-waterpolo.com/api/Competitions/{self.current_season["code"]}?{{}}='

		response = requests.get(url, headers=headers).json()

		matches = response['matches']
		games = []

		for match in matches:

			# 2022-11-15T18:30:00+01:00
			date_str = match['startDate'].split('+')[0]
			if '.' in date_str:
				date_str = date_str.split('.')[0]

			game_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')

			try:
				game_round = int(match['number'])
			except TypeError:
				game_round = None

			if match['status'] == 'Finished':
				status = PLAYED
			elif match['status'] == 'Not_Started':
				status = SCHEDULED
			else:
				logger.warning(f'Could not recognize game status "{match["status"]}"')
				status = None

			home_score = match['homeTeamGoalsTotal']
			away_score = match['awayTeamGoalsTotal']

			website_id = match['id']
			game_url = f'https://total-waterpolo.com/tw_match/{website_id}'

			home_team = unidecode(match['homeTeamDisplayName'])
			away_team = unidecode(match['awayTeamDisplayName'])

			home_id = match['homeTeamId']
			away_id = match['awayTeamId']

			team_map = {
				home_id: home_team,
				away_id: away_team
			}

			for team_id in team_map:
				if team_map[team_id] not in self.current_season['teams']:
					# print(team_id)

					for team_raw in response['competitionTeams']:
						if team_raw['teamId'] == team_id:
							team = {
								'name': team_map[team_id],
								'abbreviation': team_raw['team']['shortName'],
								'gender': team_raw['team']['gender'],
								'category': team_raw['team']['category'],
								'club': team_raw['team']['club'],
								'country': team_raw['team']['country'],
								'city': team_raw['team']['city'],
							}
							# print(team)
							self.current_season['teams'][team_map[team_id]] = team
							break

					if team_map[team_id] not in self.current_season['teams']:
						self.current_season['teams'][team_map[team_id]] = dict()
			# print(team_id)
			game = {
				'game_id': None,
				'edition_id': None,
				'date': game_date,
				# 'type': game_type,
				# 'phase': phase,
				'round': game_round,
				'status': status,
				'home_team_id': None,
				'away_team_id': None,
				'home_score': home_score,
				'away_score': away_score,
				'number_of_overtimes': None,
				'website_id': website_id,
				'game_url': game_url,
				'home_team': home_team,
				'away_team': away_team,
			}

			games.append(game)

		return games

	def get_team_details(self, team_name: str):
		season = self.current_season

		team_raw = self.current_season['teams'][team_name]

		if 'abbreviation' in team_raw:
			abbr = team_raw['abbreviation']
		else:
			abbr = None
		if 'logo' in team_raw:
			logo = team_raw['logo']
		else:
			logo = None
		if 'color' in team_raw:
			color = team_raw['color']
		else:
			color = None
		if 'gender' in team_raw:
			gender = team_raw['gender']
		else:
			gender = None
		if 'category' in team_raw:
			category = team_raw['category']
		else:
			category = None


		team = {
			'team_id': None,
			'franchise_id': None,
			'season_id': season['season_id'],
			'gender': gender,
			'category': category,
			'name': team_name,
			'abbreviation': abbr,
			'logo_url': logo,
			'color': color
		}

		return team

	def get_franchise(self, team_name: str):
		season = self.current_season

		# print(self.current_season['teams'])

		team_raw = self.current_season['teams'][team_name]

		if 'club' in team_raw:
			club = team_raw['club']
		else:
			club = team_name

		if 'city' in team_raw:
			city = team_raw['city']
		else:
			city = None

		if 'country' in team_raw:
			country = team_raw['country']
		else:
			country = None

		if 'state' in team_raw:
			state = team_raw['state']
		else:
			state = None

		franchise = {
			'franchise_id': None,
			'name': club,
			'city': city,
			'state': state,
			'country': country,
		}

		return franchise

	def download_actions(self):
		game = self.current_game

		info_url = f'https://arena.total-waterpolo.com/api/Matches/{game["website_id"]}?{{}}='
		info_response = requests.get(info_url, headers=headers).json()
		teams_map = {
			info_response['homeTeam']['id']: info_response['homeTeam']['name'],
			info_response['awayTeam']['id']: info_response['awayTeam']['name'],
		}

		# print(teams_map)

		players_map = {}

		for player_raw in info_response['players']:
			player_id = player_raw['playerId']
			name = self.clean_name(player_raw['player']['name'])
			surname = self.clean_name(player_raw['player']['surname'])
			full_name = f'{name} {surname}'
			if player_raw['player']['height'] is not None:
				height = utils.parse_int(player_raw['player']['height'].split()[0], None)
			else:
				height = None
			if player_raw['player']['weight'] is not None:
				weight = utils.parse_int(player_raw['player']['weight'].split()[0], None)
			else:
				weight = None

			role = player_raw['position']
			hand = player_raw['player']['dominantHand']
			team = player_raw['team']['name']
			number = player_raw['number']

			player = {
				'name': name,
				'surname': surname,
				'full_name': full_name,
				'birthday': None,
				'height': height,
				'weight': weight,
				'hand': hand,
				'role': role,
			}

			contract = {
				'team': team,
				'jersey_number': number,
				'picture_url': None,
			}

			players_map[player_id] = full_name

			self.current_season['players'][player_id] = (player, contract)

		# print(players_map)

		url = f'https://arena.total-waterpolo.com/api/Events/{game["website_id"]}?{{}}='

		response = requests.get(url, headers=headers).json()

		actions = []

		home_score, away_score = 0, 0

		for entry in response:

			if entry['period'] == 'First_Period':
				period = 1
			elif entry['period'] == 'Second_Period':
				period = 2
			elif entry['period'] == 'Third_Period':
				period = 3
			elif entry['period'] == 'Fourth_Period':
				period = 4
			elif entry['period'] == 'Overtime':
				period = 5
			else:
				logger.warning(f'Could not recognize period "{entry["period"]}"')
				continue

			remaining_period_time = 60 * entry['minute'] + entry['seconds']

			action_id = entry['id']

			if entry['type'] == 'Turnover':
				description = TURNOVER
				team = teams_map[entry['turnover']['teamId']]
				player = players_map[entry['turnover']['lostPossesionPlayer']['playerId']]

				flags = map_action_flag(entry['turnover']['type'])

				action = {
					'action_id': action_id,
					'period': period,
					'remaining_period_time': remaining_period_time,
					'team': team,
					'home_score': home_score,
					'away_score': away_score,
					'player': player,
					'player_id': entry['turnover']['lostPossesionPlayer']['playerId'],
					'description': description,
					'flags': flags,
					'x': None,
					'y': None,
				}

				actions.append(action)

				if entry['turnover']['wonPossesionPlayerId'] is not None:
					player_steal = players_map[entry['turnover']['wonPossesionPlayer']['playerId']]
					team_steal = teams_map[entry['turnover']['wonPossesionPlayer']['teamId']]

					action = {
						'action_id': f'{action_id}-STL',
						'period': period,
						'remaining_period_time': remaining_period_time,
						'team': team_steal,
						'home_score': home_score,
						'away_score': away_score,
						'player': player_steal,
						'player_id': entry['turnover']['wonPossesionPlayer']['playerId'],
						'description': STEAL,
						'flags': {},
						'x': None,
						'y': None,
					}

					actions.append(action)

			elif entry['type'] == 'Card':

				if entry['card']['type'] == 'Yellow':
					description = YELLOW_CARD
				elif entry['card']['type'] == 'Red':
					description = RED_CARD
				else:
					logger.warning(f'Could not recognize card "{entry["card"]["type"]}"')
					continue

				team = teams_map[entry['card']['teamId']]
				if entry['card']['cardedPlayerId'] is not None:
					player = players_map[entry['card']['cardedPlayer']['playerId']]
					player_id = entry['card']['cardedPlayer']['playerId']
				else:
					player = None
					player_id = None

				action = {
					'action_id': action_id,
					'period': period,
					'remaining_period_time': remaining_period_time,
					'team': team,
					'home_score': home_score,
					'away_score': away_score,
					'player': player,
					'player_id': player_id,
					'description': description,
					'flags': {},
					'x': None,
					'y': None,
				}

				actions.append(action)

			elif entry['type'] == 'Timeout':
				description = TURNOVER
				team = teams_map[entry['timeout']['teamId']]

				flags = {}

				action = {
					'action_id': action_id,
					'period': period,
					'remaining_period_time': remaining_period_time,
					'team': team,
					'home_score': home_score,
					'away_score': away_score,
					'player': None,
					'player_id': None,
					'description': description,
					'flags': flags,
					'x': None,
					'y': None,
				}

				actions.append(action)

			elif entry['type'] == 'Swim_Off':
				home_player_id = entry['swimoff']['homeTeamSwimmer']['playerId']
				away_player_id = entry['swimoff']['awayTeamSwimmer']['playerId']

				if entry['swimoff']['winnerSwimmer'] is None:
					continue
				if home_player_id == entry['swimoff']['winnerSwimmer']['playerId']:
					winning_player = players_map[home_player_id]
					winning_player_id = home_player_id
					winning_team = game['home_team']

					losing_player = players_map[away_player_id]
					losing_player_id = away_player_id
					losing_team = game['away_team']
				else:
					winning_player = players_map[away_player_id]
					winning_player_id = away_player_id
					winning_team = game['away_team']

					losing_player = players_map[home_player_id]
					losing_player_id = home_player_id
					losing_team = game['home_team']

				action = {
					'action_id': action_id,
					'period': period,
					'remaining_period_time': remaining_period_time,
					'team': winning_team,
					'home_score': home_score,
					'away_score': away_score,
					'player': winning_player,
					'player_id': winning_player_id,
					'description': SWIM_OFF_WON,
					'flags': {},
					'x': None,
					'y': None,
				}

				actions.append(action)

				action = {
					'action_id': f'{action_id}-SOL',
					'period': period,
					'remaining_period_time': remaining_period_time,
					'team': losing_team,
					'home_score': home_score,
					'away_score': away_score,
					'player': losing_player,
					'player_id': losing_player_id,
					'description': SWIM_OFF_LOST,
					'flags': {},
					'x': None,
					'y': None,
				}

				actions.append(action)

			elif entry['type'] == 'Exclusion':
				description = EXCLUSION
				team = teams_map[entry['exclusion']['teamId']]
				if entry['exclusion']['excludedPlayerId'] is not None:
					player = players_map[entry['exclusion']['excludedPlayer']['playerId']]
					player_id = entry['exclusion']['excludedPlayer']['playerId']
				else:
					player = None
					player_id = None

				flags = set()
				if entry['exclusion']['isPenaltyExclusion']:
					flags.add(PENALTY_FOUL)
				if entry['exclusion']['isDoubleExclusion']:
					flags.add(DOUBLE_EXCLUSION)

				action = {
					'action_id': action_id,
					'period': period,
					'remaining_period_time': remaining_period_time,
					'team': team,
					'home_score': home_score,
					'away_score': away_score,
					'player': player,
					'player_id': player_id,
					'description': description,
					'flags': flags,
					'x': entry['exclusion']['locationX'],
					'y': entry['exclusion']['locationY'],
				}

				actions.append(action)

				if entry['exclusion']['fouledPlayerId'] is not None:
					player_drawn = players_map[entry['exclusion']['fouledPlayer']['playerId']]
					team_drawn = teams_map[entry['exclusion']['fouledPlayer']['teamId']]

					action = {
						'action_id': f'{action_id}-FD',
						'period': period,
						'remaining_period_time': remaining_period_time,
						'team': team_drawn,
						'home_score': home_score,
						'away_score': away_score,
						'player': player_drawn,
						'player_id': entry['exclusion']['fouledPlayer']['playerId'],
						'description': FOUL_DRAWN,
						'flags': flags,
						'x': entry['exclusion']['locationX'],
						'y': entry['exclusion']['locationY'],
					}

					actions.append(action)

			elif entry['type'] == 'Shot':
				if entry['shot']['isGoal']:
					description = GOAL
				else:
					description = MISS

				team = teams_map[entry['shot']['teamId']]

				if description == GOAL and team == game['home_team']:
					home_score += 1
				elif description == GOAL and team == game['away_team']:
					away_score += 1

				player = players_map[entry['shot']['takenBy']['playerId']]

				flags = map_action_flag(entry['shot']['type'])

				action = {
					'action_id': action_id,
					'period': period,
					'remaining_period_time': remaining_period_time,
					'team': team,
					'home_score': home_score,
					'away_score': away_score,
					'player': player,
					'player_id': entry['shot']['takenBy']['playerId'],
					'description': description,
					'flags': flags,
					'x': entry['shot']['locationX'],
					'y': entry['shot']['locationY'],
					'target_x': entry['shot']['locationX'],
					'target_y': entry['shot']['locationY'],
				}

				actions.append(action)

				if entry['shot']['blockedById'] is not None:
					player_block = players_map[entry['shot']['blockedBy']['playerId']]
					team_block = teams_map[entry['shot']['blockedBy']['teamId']]

					action = {
						'action_id': f'{action_id}-BLK',
						'period': period,
						'remaining_period_time': remaining_period_time,
						'team': team_block,
						'home_score': home_score,
						'away_score': away_score,
						'player': player_block,
						'player_id': entry['shot']['blockedBy']['playerId'],
						'description': BLOCK,
						'flags': flags,
						'x': entry['shot']['locationX'],
						'y': entry['shot']['locationY'],
						'target_x': entry['shot']['locationX'],
						'target_y': entry['shot']['locationY'],
					}

					actions.append(action)

					# action = {
					# 	'action_id': f'{action_id}-BLKA',
					# 	'period': period,
					# 	'remaining_period_time': remaining_period_time,
					# 	'team': team,
					# 	'home_score': home_score,
					# 	'away_score': away_score,
					# 	'player': player,
					# 	'player_id': entry['shot']['takenBy']['playerId'],
					# 	'description': BLOCK_AGAINST,
					# 	'flags': flags,
					# 	'x': entry['shot']['locationX'],
					# 	'y': entry['shot']['locationY'],
					# 	'target_x': entry['shot']['locationX'],
					# 	'target_y': entry['shot']['locationY'],
					# }
					#
					# actions.append(action)

				if entry['shot']['assistedById'] is not None:
					player_ast = players_map[entry['shot']['assistedBy']['playerId']]
					team_ast = teams_map[entry['shot']['assistedBy']['teamId']]

					action = {
						'action_id': f'{action_id}-AST',
						'period': period,
						'remaining_period_time': remaining_period_time,
						'team': team_ast,
						'home_score': home_score,
						'away_score': away_score,
						'player': player_ast,
						'player_id': entry['shot']['assistedBy']['playerId'],
						'description': ASSIST,
						'flags': flags,
						'x': entry['shot']['locationX'],
						'y': entry['shot']['locationY'],
						'target_x': entry['shot']['locationX'],
						'target_y': entry['shot']['locationY'],
					}

					actions.append(action)

				if entry['shot']['savedById'] is not None:
					player_save = players_map[entry['shot']['savedBy']['playerId']]
					team_save = teams_map[entry['shot']['savedBy']['teamId']]

					action = {
						'action_id': f'{action_id}-SAVE',
						'period': period,
						'remaining_period_time': remaining_period_time,
						'team': team_save,
						'home_score': home_score,
						'away_score': away_score,
						'player': player_save,
						'player_id': entry['shot']['savedBy']['playerId'],
						'description': SAVE,
						'flags': flags,
						'x': entry['shot']['locationX'],
						'y': entry['shot']['locationY'],
						'target_x': entry['shot']['locationX'],
						'target_y': entry['shot']['locationY'],
					}

					actions.append(action)

			elif entry['type'] is None:
				continue
			else:
				logger.warning(f'Could not recognize action type "{entry["type"]}", ignoring action')
				print(entry)
				continue
		return actions


def map_action_flag(flag):
	mapping = {
		'Clock_Expired': {CLOCK},
		'Lost_Ball': {LOST},
		'Power_Play': {LOST},
		'Penalty': {PENALTY},
		'Regular_Attack': None,
		'Offensive_Foul': {OFFENSIVE_FOUL},
		'Ball_Under': {BALL_UNDER},
	}

	if flag in mapping:
		if mapping[flag] is None:
			return {}
		else:
			return mapping[flag]
	else:
		logger.warning(f'Could not recognize action flag "{flag}"')
		return {}