from datetime import datetime
import unittest

import cache_requests
from lxml import html
from predictivepunter.scrape import scrape
import pymongo
import pypunters


class ScrapeTest(unittest.TestCase):

	def test_scrape(self):
		"""The scrape method should populate the database"""

		date_from = date_to = datetime(2016, 2, 1)

		database = pymongo.MongoClient()['predictivepunter_test']
		collections = ('meets', 'races', 'runners', 'horses', 'jockeys', 'trainers', 'performances')
		for collection in collections:
			database[collection].delete_many({})

		http_client = cache_requests.Session()
		html_parser = html.fromstring
		scraper = pypunters.Scraper(http_client, html_parser)

		scrape(date_from, date_to, database, scraper, threads=4)

		for collection in collections:
			self.assertGreater(database[collection].count(), 0)