import logging
import os
import numpy as np
import pandas as pd
from writers.writer import Writer as Abstract
from utils.constants import *
logger = logging.getLogger('sdeng')


class Writer(Abstract):

    def __init__(self, **kwargs):
        super().__init__()
        self.raw_dir_path = 'data'
        self.dir_path = None
        self.league_dir_path = None
        self.file_separator = ','
        self.decimal_separator = '.'
        self.players = dict()
        self.contracts = dict()
        self.append = 'append' in kwargs and kwargs['append']

        if 'dir' in kwargs:
            self.raw_dir_path = kwargs['dir']

        if 'csv_file_separator' in kwargs:
            self.file_separator = kwargs['csv_file_separator']

        if 'csv_decimal_separator' in kwargs:
            self.decimal_separator = kwargs['csv_decimal_separator']

    def check_and_insert_league(self, content: dict):
        self.league_dir_path = os.path.join(self.raw_dir_path, content['name'])
        return content['name']

    def check_and_insert_season(self, content: dict):
        season_code = f'{content["start"]%100:02d}-{content["end"]%100:02d}'
        self.dir_path = os.path.join(self.league_dir_path, season_code)

        if os.path.exists(self.dir_path) and not self.append:
            for f in os.listdir(self.dir_path):
                os.remove(os.path.join(self.dir_path, f))

        return season_code

    def check_and_insert_edition(self, content: dict):
        return f'{content["season_id"]} {content["league_id"]}'

    def check_and_insert_game(self, content: dict):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

        filename = os.path.join(self.dir_path, 'games.csv')

        if not content:
            return

        columns_order = ['season_id', 'edition_id', 'game_id', 'website_id', 'date', 'round',
                         'status', 'home_team_id', 'away_team_id', 'home_score', 'away_score']

        game_id = f'{content["date"].date()}:{content["home_team_id"]}-{content["away_team_id"]}'
        content['game_id'] = game_id

        df = pd.DataFrame([content])
        df = df[columns_order]

        if not os.path.exists(filename):
            df.to_csv(filename, index=False, sep=self.file_separator)
        else:
            df.to_csv(filename, index=False, sep=self.file_separator, mode='a', header=False)

        return game_id

    def check_and_insert_team(self, content: dict):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

        filename = os.path.join(self.dir_path, 'teams.csv')

        if not content:
            return

        columns_order = ['team_id', 'franchise_id', 'season_id', 'conference', 'gender', 'category', 'name', 'abbreviation', 'logo_url', 'color']

        content['team_id'] = content['name']

        if 'conference' not in content:
            content['conference'] = None

        df = pd.DataFrame([content])
        df = df[columns_order].drop_duplicates()

        if not os.path.exists(filename):
            df.to_csv(filename, index=False, sep=self.file_separator)
        else:
            df.to_csv(filename, index=False, sep=self.file_separator, mode='a', header=False)

        return content["name"]

    def check_and_insert_franchise(self, content: dict):
        return content['name']

    def check_and_insert_edition_participant(self, content: dict):
        return None

    def check_and_insert_actions(self, actions):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

        filename = os.path.join(self.dir_path, 'play_by_play.csv')

        if not actions:
            return

        df = pd.DataFrame(actions)

        df = df.convert_dtypes()
        s = df.select_dtypes(include='Float64').columns
        df[s] = df[s].astype("float")

        if not os.path.isfile(filename):
            df.to_csv(filename, header=True, index=False, float_format='%.3f', sep=self.file_separator, decimal=self.decimal_separator)
        else:
            df.to_csv(filename, mode='a', header=False, index=False, float_format='%.3f', sep=self.file_separator, decimal=self.decimal_separator)

    def insert_player_and_contract(self, player, contract):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)

        filename = os.path.join(self.dir_path, 'rosters.csv')

        if not player or not contract:
            return
        if 'name' not in player or 'surname' not in player:
            logger.error(f'Player {player["full_name"]} has no name or surname')
            exit()

        player_id = player['full_name']
        player['player_id'] = player_id
        contract['player_id'] = player_id

        df = pd.DataFrame([player | contract])

        columns_order = ['player_id', 'name', 'surname', 'full_name', 'birthday', 'role', 'height', 'weight', 'hand', 'team_id', 'season_id', 'jersey_number',
                         'picture_url']

        # df = df.sort_values(axis=0, by=columns_order)
        df = df[columns_order]

        if not os.path.exists(filename):
            df.to_csv(filename, index=False, sep=self.file_separator)
        else:
            df.to_csv(filename, index=False, sep=self.file_separator, mode='a', header=False)

        return player_id
