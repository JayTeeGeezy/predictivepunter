from datetime import datetime
from getopt import getopt
import locale
import logging
import subprocess
import sys

import cache_requests
from lxml import html
import pymongo
import pypunters
import pyracing


class CommandLineProcessor(pyracing.Processor):
	"""Extend the pyracing Processor class with command-line functionality"""

	@classmethod
	def get_configuration(cls, args):
		"""Return a dictionary of configuration values based on the provided command-line arguments"""

		configuration = {
			'backup_database':	False,
			'cache_expiry':		60 * 10,	# 10 minutes
			'database_name':	'predictivepunter',
			'date_from':		datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
			'date_to':			datetime.today().replace(hour=0, minute=0, second=0, microsecond=0),
			'logging_level':	logging.INFO,
			'threads':			4
		}

		opts, args = getopt(args, 'bd:n:qt:vx:', ['backup-database', 'date=', 'database-name=', 'quiet', 'threads=', 'verbose', 'cache-expiry='])

		for opt, arg in opts:

			if opt in ('-b', '--backup-database'):
				configuration['backup_database'] = True

			elif opt in ('-d', '--date'):
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

	def __init__(self, backup_database=False, cache_expiry=600, database_name='predictivepunter', logging_level=logging.INFO, message_prefix='processing', threads=4, *args, **kwargs):
		"""Initialize instance dependencies"""

		self.backup_database = backup_database
		self.cache_expiry = cache_expiry
		self.database_name = database_name
		self.logging_level = logging_level

		logging.basicConfig(level=self.logging_level)

		self.database = pymongo.MongoClient()[self.database_name]
		self.database_has_changed = False

		self.http_client = cache_requests.Session(ex=self.cache_expiry)
		self.html_parser = html.fromstring
		self.scraper = pypunters.Scraper(self.http_client, self.html_parser)

		pyracing.initialize(self.database, self.scraper)
		for entity in (Seed, Prediction):
			entity.initialize()
		for entity in ('meet', 'race', 'runner', 'horse', 'jockey', 'trainer', 'performance', 'seed', 'prediction'):
			pyracing.add_subscriber('saved_' + entity, self.handle_saved_event)

		super().__init__(threads=threads, message_prefix=message_prefix)

	def handle_saved_event(self, entity):
		"""Record the fact that the database has changed when an entity is saved"""

		self.database_has_changed = True

	def dump_database(self):
		"""Dump the database to the filesystem"""

		if self.database_has_changed:
			subprocess.check_call('mongodump --db {name}'.format(name=self.database_name), shell=True)
			self.database_has_changed = False

	def post_process_date(self, date):
		"""Handle the post_process_date event"""

		if self.backup_database:
			self.dump_database()


try:
	from .seed import Seed
	from .predict import Prediction
except SystemError:
	from seed import Seed
	from predict import Prediction