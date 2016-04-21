from datetime import datetime
from getopt import getopt
import locale
import logging
import sys

import cache_requests
from lxml import html
import pymongo
import pypunters
import pyracing


def do_nothing(item):
	pass

def get_configuration(args):
	"""Return a dictionary of configuration values based on the supplied command-line arguments"""

	configuration = {
		'cache_expiry':		60 * 10,	# 10 minutes
		'database_name':	'predictivepunter',
		'date_from':		datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
		'date_to':			datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
		'logging_level':	logging.INFO,
		'threads':			4
	}

	opts, args = getopt(args, 'd:n:qt:vx:', ['date=', 'database-name=', 'quiet', 'threads=', 'verbose', 'cache-expiry='])

	for opt, arg in opts:

		if opt in ('-d', '--date'):
			dates = [datetime.strptime(value, locale.nl_langinfo(locale.D_FMT)) for value in arg.split('-')]
			if len(dates) > 0:
				configuration['date_from'] = configuration['date_to'] = dates[-1]
				if len(dates) > 1:
					configuration['date_from'] = dates[0]

		elif opt in ('-n', '--database-name'):
			configuration['database_name'] = arg

		elif opt in ('-q', '--quiet'):
			configuration['logging_level'] = logging.WARNING

		elif opt in ('-t', '--threads'):
			configuration['threads'] = int(arg)

		elif opt in ('-v', '--verbose'):
			configuration['logging_level'] = logging.DEBUG

		elif opt in ('-x', '--cache-expiry'):
			configuration['cache_expiry'] = int(arg)

	return configuration

def initialize(configuration):
	"""Initialize module dependencies based on provided configuration values"""

	logging.basicConfig(level=configuration['logging_level'])

	database = pymongo.MongoClient()[configuration['database_name']]

	http_client = cache_requests.Session(ex=configuration['cache_expiry'])
	html_parser = html.fromstring
	scraper = pypunters.Scraper(http_client, html_parser)

	return database, scraper

def main():
	"""The main entry point for the command-line utility"""

	locale.setlocale(locale.LC_ALL, '')
	config = get_configuration(sys.argv[1:])

	database, scraper = initialize(config)

	scrape(config['date_from'], config['date_to'], database, scraper, config['threads'])

def scrape(date_from, date_to, database, scraper, threads=1):
	"""Scrape all racing data for the specified date range"""

	pyracing.initialize(database, scraper)
	
	handlers = {}
	for key1 in ('date', 'meet', 'race', 'runner', 'horse'):
		for key2 in ('pre', 'post'):
			handlers[key1 + '_' + key2 + '_processor'] = do_nothing
	for key in ('jockey', 'trainer', 'performance'):
		handlers[key + '_processor'] = do_nothing
	iterator = pyracing.Iterator(threads=threads, message_prefix='scraping', **handlers)

	iterator.process_dates(date_from, date_to)


if __name__ == '__main__':
	main()