import logging
from abc import ABC, abstractmethod
import yaml
logger = logging.getLogger('sdeng')


class Writer(ABC):
    def __init__(self):
        self.mappings = dict()
        return

    @abstractmethod
    def check_and_insert_league(self, content: dict):
        pass

    @abstractmethod
    def check_and_insert_season(self, content: dict):
        pass

    @abstractmethod
    def check_and_insert_edition(self, content: dict):
        pass

    @abstractmethod
    def check_and_insert_game(self, content: dict):
        pass

    @abstractmethod
    def check_and_insert_team(self, content: dict):
        pass

    @abstractmethod
    def check_and_insert_franchise(self, content: dict):
        pass

    @abstractmethod
    def check_and_insert_edition_participant(self, content: dict):
        pass

    @abstractmethod
    def check_and_insert_actions(self, actions):
        pass

    @abstractmethod
    def insert_player_and_contract(self, player, contract):
        pass

    def get_mapping(self, mapping_name, directory='mappings'):
        path = f'writers/res/{directory}/{mapping_name}.yml'

        if mapping_name not in self.mappings:
            try:
                file = open(path, 'rb')
                mapping = yaml.safe_load(file)
                file.close()

                self.mappings[mapping_name] = mapping
            except FileNotFoundError:
                logger.warning(f'There is no file {mapping_name}, in the resource file, this mapping will not be considered')
                self.mappings[mapping_name] = dict()

        return self.mappings[mapping_name]

