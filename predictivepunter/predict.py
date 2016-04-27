import locale
import sys
import threading

import numpy
import pyracing
from sklearn import cross_validation, ensemble

try:
	from .common import CommandLineProcessor
	from .seed import Seed
except SystemError:
	from common import CommandLineProcessor
	from seed import Seed


class Prediction(pyracing.Entity):
	"""A prediction represents a machine learning system's prediction of a race's result"""

	PREDICTION_VERSION = 1
	TEST_SIZE = 0.20

	predictor_cache = {}
	predictor_cache_lock = threading.RLock()

	@classmethod
	def clear_predictor_cache(cls):
		"""Remove all cached predictors"""

		if isinstance(cls.predictor_cache, dict):
			for key in cls.predictor_cache:
				del cls.predictor_cache[key]
		else:
			cls.predictor_cache = {}

	@classmethod
	def get_earliest_date(cls):
		"""Return the earliest date for any meet in the database"""

		return pyracing.Meet.get_database_collection().find().sort('date')[0]['date']

	@classmethod
	def get_prediction_by_id(cls, id):
		"""Get the single prediction with the specified database ID"""

		return cls.find_one({'_id': id})

	@classmethod
	def get_prediction_by_race(cls, race):
		"""Get the prediction for the specified race"""

		return cls.find_or_scrape_one(
			filter={'race_id': race['_id'], 'earliest_date': cls.get_earliest_date(), 'prediction_version': cls.PREDICTION_VERSION, 'seed_version': Seed.SEED_VERSION},
			scrape=cls.generate_prediction,
			scrape_args=[race],
			expiry_date=None
			)

	@classmethod
	def generate_prediction(cls, race):
		"""Generate a prediction for the specified race"""

		results = None
		score = None

		predictor = None
		generate_predictor = False

		segment = tuple(race['entry_conditions']) + tuple([race['track_condition']])
		with cls.predictor_cache_lock:
			if segment in cls.predictor_cache:
				predictor = cls.predictor_cache[segment]
			else:
				cls.predictor_cache[segment] = None
				generate_predictor = True

		if generate_predictor:

			similar_races = pyracing.Race.find({
				'entry_conditions': race['entry_conditions'],
				'track_condition':	race['track_condition'],
				'start_time':		{'$lt': race.meet['date']}
				})
			if len(similar_races) >= (1 / cls.TEST_SIZE):

				try:

					train_races, test_races = cross_validation.train_test_split(similar_races, test_size=cls.TEST_SIZE)

					train_X = []
					train_y = []
					train_weights = []
					for race in train_races:
						for runner in race.runners:
							if runner.result is not None:
								train_X.append(Seed.get_seed_by_runner(runner).normalized_data)
								train_y.append(runner.result)
								train_weights.append(race.importance)

					test_X = []
					test_y = []
					test_weights = []
					for race in test_races:
						for runner in race.runners:
							if runner.result is not None:
								test_X.append(Seed.get_seed_by_runner(runner).normalized_data)
								test_y.append(runner.result)
								test_weights.append(race.importance)

					classifier = ensemble.GradientBoostingRegressor()
					classifier.fit(train_X, train_y, train_weights)

					predictor = {
						'classifier':	classifier,
						'score':		classifier.score(test_X, test_y, test_weights)
					}
					cls.predictor_cache[segment] = predictor

				except:

					del cls.predictor_cache[segment]
					raise

			else:

				del cls.predictor_cache[segment]

		else:

			while predictor is None:
				try:
					predictor = cls.predictor_cache[segment]
				except KeyError:
					break

		if predictor is not None:

			if 'classifier' in predictor and predictor['classifier'] is not None:
				raw_results = {}
				for runner in race.runners:
					raw_result = predictor['classifier'].predict(numpy.array(Seed.get_seed_by_runner(runner).normalized_data).reshape(1, -1))[0]
					if raw_result is not None:
						if not raw_result in raw_results:
							raw_results[raw_result] = []
						raw_results[raw_result].append(runner['number'])
				for key in sorted(raw_results.keys()):
					if results is None:
						results = []
					results.append(sorted([number for number in raw_results[key]]))

			if 'score' in predictor:
				score = predictor['score']
		
		return {
			'race_id':				race['_id'],
			'earliest_date':		cls.get_earliest_date(),
			'prediction_version':	cls.PREDICTION_VERSION,
			'seed_version':			Seed.SEED_VERSION,
			'results':				results,
			'score':				score
		}

	@classmethod
	def initialize(cls):
		"""Initialize class dependencies"""

		def handle_deleting_race(race):
			for prediction in cls.find({'race_id': race['_id']}):
				prediction.delete()

		cls.event_manager.add_subscriber('deleting_race', handle_deleting_race)

		cls.create_index([('race_id', 1), ('earliest_date', 1), ('prediction_version', 1), ('seed_version', 1)])

	def __str__(self):

		return 'prediction for race {race}'.format(race=self.race)

	@property
	def race(self):
		"""Return the race to which this prediction applies"""

		if not 'race' in self.cache:
			self.cache['race'] = pyracing.Race.get_race_by_id(self['race_id'])
		return self.cache['race']


class PredictProcessor(CommandLineProcessor):
	"""Populate the database with predictions for all runners in the specified date range"""

	def __init__(self, *args, **kwargs):
		"""Initialize instance dependencies"""

		super().__init__(message_prefix='predicting', *args, **kwargs)

	def pre_process_date(self, date):
		"""Handle the pre_process_date event by clearing the predictor cache"""

		Prediction.clear_predictor_cache()

	def post_process_race(self, race):
		"""Handle the post_process_race event by creating a prediction for the race"""
		
		Prediction.get_prediction_by_race(race)


def main():
	"""Main entry point for the scrape console script"""

	locale.setlocale(locale.LC_ALL, '')

	configuration = PredictProcessor.get_configuration(sys.argv[1:])

	processor = PredictProcessor(**configuration)
	processor.process_dates(date_from=configuration['date_from'], date_to=configuration['date_to'])


if __name__ == '__main__':
	main()