import argparse
import logging
from datetime import datetime
import sys
from utils.constants import *
logger = logging.getLogger('waterpolo')


# Creating a handler
def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
	if issubclass(exc_type, KeyboardInterrupt):
		# Will call default excepthook
		sys.__excepthook__(exc_type, exc_value, exc_traceback)
		return
		# Create a critical level log message with info from the except hook.
	logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))


# Assign the excepthook to the handler
sys.excepthook = handle_unhandled_exception


def get_writer(name, **kwargs):
	name = name.lower()
	# if name == 'mysql':
	# 	from writers.MySQL.writer import Writer
	# 	writer = Writer(**kwargs)
	if name == 'csv':
		from writers.CSV.writer import Writer
		writer = Writer(**kwargs)
	# elif name == 'parquet' or name == 'pq':
	# 	from writers.parquet.writer import Writer
	# 	writer = Writer(**kwargs)
	# elif name == 'sqlite3' or name == 'sqlite':
	# 	from writers.SQLite3.writer import Writer
	# 	writer = Writer(**kwargs)
	else:
		writer = None

	return writer


def get_scraper(name, writer):
	name = name.upper()
	if name == 'LEN':
		from scrapers.leagues.LEN import Scraper
	elif name == 'WC':
		from scrapers.leagues.WC import Scraper
	elif name == 'EC':
		from scrapers.leagues.EC import Scraper
	else:
		return None

	scraper = Scraper(writer)

	return scraper


def main():
	parser = argparse.ArgumentParser()

	leagues = [
		'- LEN: LEN Champions League',
	]
	leagues_str = '\n'.join(sorted(leagues))

	league_help = f'The leagues to save. Allowed leagues are:\n{leagues_str}'
	parser.add_argument('-l', '--leagues', nargs='+', required=True, help=league_help)

	writer_choiches = ['mysql', 'csv', 'sqlite3', 'sqlite', 'parquet', 'pq']
	writer_help = f'The writer to use.'
	parser.add_argument('-w', '--writer', required=True, help=writer_help, choices=writer_choiches)

	seasons_help = 'The seasons to save in the format starting_year-ending_year (ex: 2021-2022, 2022-2023)'
	parser.add_argument('-s', '--seasons', nargs='+', help=seasons_help, default=[])

	types_help = 'The type of the game, such as RS or PO'
	parser.add_argument('-t', '--types', nargs='+', help=types_help)

	phases_help = 'The type of the game, RS for regular season games, 4F, 2F, F'
	parser.add_argument('-p', '--phases', nargs='+', help=phases_help)

	rounds_help = 'The round of the game'
	parser.add_argument('-r', '--rounds', nargs='+', type=int, help=rounds_help)

	ids_help = 'The id of the game'
	parser.add_argument('-i', '--website_ids', nargs='+', type=str, help=ids_help)

	start_date_help = 'The first date to consider (included) in the format year-month-day (ex: 2021-9-15)'
	parser.add_argument('--start_date', '--start', type=str, help=start_date_help)

	end_date_help = 'The last date to consider (included) in the format year-month-day (ex: 2021-9-15)'
	parser.add_argument('--end_date', '--end', type=str, help=end_date_help)

	date_help = 'The date to consider (included) in the format year-month-day (ex: 2021-9-15)'
	parser.add_argument('-D', '--date', type=str, help=date_help)

	status_help = 'The status of the game; default is \'played\'. It can take more than one argument.'
	parser.add_argument('--status', nargs='+', help=status_help, default=['played'])

	status_help = 'The teams in the game'
	parser.add_argument('-T', '--teams', nargs='+', help=status_help, default=[])

	mysql_config_help = 'The path of mysql config file'
	parser.add_argument('--mysql_config', type=str, default='writers/MySQL/config.yaml', help=mysql_config_help)

	csv_dir_help = 'The directory where to store the csv or parquet files'
	parser.add_argument('--dir', '--csv_dir', '--parquet_dir', type=str, default='data', help=csv_dir_help)

	csv_append_help = 'Whether to append the content to a previously existing file, or delete it and create it from scratch. The default behavior is to delete'
	parser.add_argument('-a', '--append', default=False, help=csv_append_help, action='store_true')

	boxscores_only_help = 'Whether to save only the boxscores, ignoring play-by-play logs. Default is false.'
	parser.add_argument('--no_pbp', '--no_play-by-play', '--boxscores_only', '--boxscore_only', default=False,
	                    help=boxscores_only_help, action='store_true')

	parser.add_argument('--suppress_warnings', default=False, help='Suppress warnings on missing franchises or abbrevations', action='store_true')

	low_bandwidth_help = 'Whether to use less internet. Default is false.'
	parser.add_argument('-S', '--low_bandwidth', '--save', default=False, help=low_bandwidth_help, action='store_true')

	csv_decimal_separator_help = 'The separator of decimal numbers in csv files, default is \'.\''
	parser.add_argument('--csv_decimal_separator', type=str, default='.', help=csv_decimal_separator_help)

	csv_file_separator_help = 'The separator of csv files, default is \',\''
	parser.add_argument('--csv_file_separator', type=str, default=',', help=csv_file_separator_help)

	sqlite3_db_help = 'The path to the SQLite3 database file'
	parser.add_argument('--sqlite3_db', type=str, default='writers/SQLite3/sdeng.db', help=sqlite3_db_help)

	parser.add_argument('-d', '--debug', help='Print lots of debugging statements', action='store_const',
	                    dest='loglevel', const=logging.DEBUG, default=logging.WARNING)
	parser.add_argument('-v', '--verbose', help='Be verbose', action='store_const', dest='loglevel', const=logging.INFO)

	parser.add_argument('--tg', help='Log to telegram', action='store_true', default=False)
	parser.add_argument('--tg_config', help='The yaml config file containing info about the telegram logger bot',
	                    type=str, default='loggers/telegram/config.yml')

	args = parser.parse_args()
	logger.setLevel(level=args.loglevel)

	tg_config = dict()
	if args.tg is True:
		import tg_logger
		import yaml
		try:
			with open(args.tg_config) as f:
				tg_config = yaml.safe_load(f)
				tg_logger.setup(logger, token=tg_config['token'], users=tg_config['users'])

		except FileNotFoundError:
			logger.warning(f'Could not find file {args.tg_config}. Won\'t setup telegram logger')
		except KeyError:
			logger.warning(
				f'Something is wrong in the {args.tg_config} file. Please check that both "token" and "users" keys are present')

	if args.start_date:
		try:
			start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
		except ValueError:
			start_date = None
	else:
		start_date = None

	if args.end_date:
		try:
			end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
		except ValueError:
			end_date = None
	else:
		end_date = None

	if args.date:
		try:
			end_date = datetime.strptime(args.date, '%Y-%m-%d')
			start_date = datetime.strptime(args.date, '%Y-%m-%d')
		except ValueError:
			pass

	seasons = []
	for season in args.seasons:
		if len(season) == 9:
			seasons.append(season)

		elif len(season) == 5:
			start = int(season[0:2])
			end = int(season[3:5])
			if start == 99:
				start = 1999
				end = 2000
			elif start >= 70:
				start = 1900 + start
				end = 1900 + end
			else:
				start = 2000 + start
				end = 2000 + end

			seasons.append(f'{start}-{end}')

	kwargs = {
		'seasons': seasons,
		'types': args.types,
		'phases': args.phases,
		'rounds': args.rounds,
		'website_ids': args.website_ids,
		'status': args.status,
		'start_date': start_date,
		'end_date': end_date,
		'teams': args.teams,
		'no_pbp': args.no_pbp,
		'low_bandwidth': args.low_bandwidth,
		'tg': args.tg,
		'tg_config': tg_config,
		'suppress_warnings': args.suppress_warnings,
	}

	kwargs_writer = {
		'config_file': args.mysql_config,
		'dir': args.dir,
		'append': bool(args.append),
		'csv_file_separator': args.csv_file_separator,
		'csv_decimal_separator': args.csv_decimal_separator,
		'sqlite_db': args.sqlite3_db,
	}

	writer = get_writer(args.writer, **kwargs_writer)
	if writer is None:
		logger.error(f'Writer {args.writer} is not within allowed values [mysql, csv, sqlite3]. Closing.')
		exit(UNSUPPORTED_WRITER)

	for league in args.leagues:
		scraper = get_scraper(name=league, writer=writer)

		if scraper is None:
			logger.error(f'League {league} is not within allowed values. Currently, supported leagues are\n{leagues_str}')
			continue

		scraper.download(**kwargs)

	exit(0)


if __name__ == '__main__':
	main()
