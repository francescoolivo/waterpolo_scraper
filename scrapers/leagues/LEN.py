from scrapers.general.Waterpolo import Scraper as AbstractScraper
import logging

logger = logging.getLogger('waterpolo')


class Scraper(AbstractScraper):

	def __init__(self, writer):
		season_map = {
			2022: 2124
		}
		super().__init__(writer, season_map)

	def get_league(self):
		return {
			'full_name': 'LEN Champions League',
			'name': 'LEN',
			'website': 'total-waterpolo.com/len-champions-league-2022-23/',
			# 'international': 0,
			# 'type': DOMESTIC_LEAGUE,
			# 'tier': 1,
			# 'league_dir': 'LNB'
		}
