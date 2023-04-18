import re
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from utils.constants import *


def get_soup(url: str, headers=None, params=None, verify=True):
    requests.packages.urllib3.disable_warnings()
    session = requests.Session()
    retry = Retry(connect=10, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    try:
        response = requests.get(url, headers=headers, params=params, verify=verify).text
        soup = BeautifulSoup(response, 'lxml')
        counter = 0
        while soup is None and counter < 10:
            response = session.get(url, headers=headers, params=params, verify=verify).text
            soup = BeautifulSoup(response, 'lxml')
            counter += 1
        return soup
    except requests.exceptions.ChunkedEncodingError as e:
        return None
    except Exception as e:
        print(e)
        return None


def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False


def is_soup_valid(soup: BeautifulSoup):
    return not soup.find('div', class_='alert')


def get_general_type(action_type: str, flags: set):
    if action_type in [GOAL]:
        return 'goal'
    elif action_type in [MISS]:
        return 'miss'
    elif action_type == EXCLUSION:
        return 'foul'
    elif action_type == TURNOVER:
        return 'turnover'
    elif action_type == SWIM_OFF_WON:
        return 'swimoff'
    else:
        return


def get_referenced_types(general_type):
    types_map = {
        'goal': {ASSIST, SAVE},
        'miss': {BLOCK, SAVE},
        'turnover': {STEAL},
        'foul': {FOUL_DRAWN},
        'swimoff': {SWIM_OFF_LOST},
    }
    if general_type in types_map:
        return types_map[general_type]
    else:
        return {}


def get_closing_types(general_type):
    types_map = {
        'goal': {},
        'miss': {},
        'turnover': {STEAL},
        'foul': {FOUL_DRAWN},
        'swimoff': {SWIM_OFF_LOST},
    }
    if general_type in types_map:
        return types_map[general_type]
    else:
        return {}


def get_ignored_types(general_type):
    types_map = {
        'goal': {},
        'miss': {},
        'turnover': {},
        'foul': {},
        'swimoff': {},
    }
    if general_type in types_map:
        return types_map[general_type]
    else:
        return {}


def strings_similarity(name: str, target: str):
    name_list = name.lower().split()
    target_list = target.lower().split()
    intersection = len(list(set(name_list).intersection(target_list)))
    return float(intersection) / len(set(name_list))


def split_name_and_middle_name(name_1: str, name_2: str):
    # To avoid errors in the case Vince / Vincent and similar
    if len(name_1.split()) == 1 and len(name_2.split()) == 1:
        return name_1 if len(name_1) >= len(name_2) else name_2, None

    longest_name = name_1 if len(name_1) >= len(name_2) else name_2
    shortest_name = name_1 if len(name_1) < len(name_2) else name_2

    name_list, middle_name_list = [], []

    for subname in longest_name.split():
        if subname in shortest_name.split():
            name_list.append(subname)
        else:
            middle_name_list.append(subname)

    name = ' '.join(name_list)
    middle_name = ' '.join(middle_name_list)

    return name, middle_name


def is_name_the_same(name_1: str, name_2: str):
    return is_name_fully_contained(name_1, name_2) or is_name_fully_contained(name_2, name_1)


def is_name_fully_contained(name: str, target: str):
    counter = 0
    for subname in name.split():
        if subname in target.split():
            counter += 1

    return counter == len(name.split())


def parse_int(string, default_fill=0):
    try:
        return int(string)
    except ValueError:
        return default_fill
    except TypeError:
        return default_fill



def clean_surname_case(surname: str):
    def replace_nth(string, sub, wanted, n):
        where = [m.start() for m in re.finditer(sub, string)][n - 1]
        before = string[:where]
        after = string[where:]
        after = after.replace(sub, wanted, 1)
        new_string = before + after
        return new_string

    if surname.startswith('Mc'):
        if surname[2] == 'c':
            return replace_nth(surname, surname[2], surname[2].upper(), 2)
        else:
            return surname.replace(surname[2], surname[2].upper(), 1)
    else:
        return surname


def get_national_team_franchise(team_name):
    franchise = \
        {
            'franchise_id': None,
            'name': team_name,
            'city': None,
            'state': None,
            'country': team_name,
            'national_team': 1
        }

    return franchise
