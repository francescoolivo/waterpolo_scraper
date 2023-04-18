from scrapers.general.Waterpolo import Scraper as AbstractScraper
import logging

logger = logging.getLogger('waterpolo')


class Scraper(AbstractScraper):

	def __init__(self, writer):
		season_map = {
			2022: 2113
		}
		super().__init__(writer, season_map)

	def get_league(self):
		return {
			'full_name': 'European Championship',
			'name': 'EC',
			'website': 'https://total-waterpolo.com/len-europan-championships-split-2022-men/',
			# 'international': 0,
			# 'type': DOMESTIC_LEAGUE,
			# 'tier': 1,
			# 'league_dir': 'LNB'
		}
