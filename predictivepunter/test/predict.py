from datetime import datetime
import logging
import os
import shutil
import unittest

import cache_requests
from lxml import html
from predictivepunter.predict import PredictProcessor
import pymongo
import pypunters


class PredictProcessorTest(unittest.TestCase):

	def test_predict(self):
		"""The predict method should populate the database with predictions"""

		configuration = {
			'backup_database':	True,
			'cache_expiry':		60 * 10,	# 10 minutes
			'database_name':	'predictivepunter_test',
			'date_from':		datetime(2016, 2, 1),
			'date_to':			datetime(2016, 2, 1),
			'logging_level':	logging.DEBUG,
			'threads':			4
		}

		database = pymongo.MongoClient()[configuration['database_name']]
		database['predictions'].delete_many({})
		dump_directory = 'dump/{name}'.format(name=configuration['database_name'])
		if os.path.isdir(dump_directory):
			shutil.rmtree(dump_directory)

		processor = PredictProcessor(**configuration)
		processor.process_dates(configuration['date_from'], configuration['date_to'])

		self.assertGreater(database['predictions'].count(), 0)
		self.assertTrue(os.path.isdir(dump_directory))