from scrapers.general.Waterpolo import Scraper as AbstractScraper
import logging

logger = logging.getLogger('waterpolo')


class Scraper(AbstractScraper):

	def __init__(self, writer):
		season_map = {
			2022: 2116
		}
		super().__init__(writer, season_map)

	def get_league(self):
		return {
			'full_name': 'World Cup',
			'name': 'WC',
			'website': 'total-waterpolo.com/fina-world-championships-budapest-2022-men-livescore/',
			# 'international': 0,
			# 'type': DOMESTIC_LEAGUE,
			# 'tier': 1,
			# 'league_dir': 'LNB'
		}
