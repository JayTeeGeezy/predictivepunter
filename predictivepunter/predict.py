import locale
import sys
import threading
import time

from jtgpy.threaded_queues import QueuedCsvWriter
import numpy
import pyracing
from sklearn import cross_validation, feature_selection, pipeline, svm

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

		prediction = {
			'race_id':				race['_id'],
			'earliest_date':		cls.get_earliest_date(),
			'prediction_version':	cls.PREDICTION_VERSION,
			'seed_version':			Seed.SEED_VERSION,
			'results':				None,
			'score':				None,
			'train_seeds':			None,
			'test_seeds':			None
		}

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
					for race in train_races:
						for seed in race.seeds:
							if seed['result'] is not None:
								train_X.append(seed.normalized_data)
								train_y.append(seed['result'])

					test_X = []
					test_y = []
					for race in test_races:
						for seed in race.seeds:
							if seed['result'] is not None:
								test_X.append(seed.normalized_data)
								test_y.append(seed['result'])

					predictor = {
						'classifier':	None,
						'score':		None,
						'train_seeds':	len(train_y),
						'test_seeds':	len(test_y)
					}
					dual = len(train_X) < len(train_X[0])
					kernel = 'linear'
					loss = 'epsilon_insensitive'
					if not dual:
						loss = 'squared_epsilon_insensitive'
					for estimator in (
						svm.SVR(kernel=kernel),
						svm.LinearSVR(dual=dual, loss=loss),
						svm.NuSVR(kernel=kernel)
						):

						classifier = pipeline.Pipeline([
							('feature_selection', feature_selection.SelectFromModel(estimator, 'mean')),
							('regression', estimator)
							])
						classifier.fit(train_X, train_y)
						score = classifier.score(test_X, test_y)

						if predictor['classifier'] is None or predictor['score'] is None or score > predictor['score']:
							predictor['classifier'] = classifier
							predictor['score'] = score

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
					time.sleep(10)
				except KeyError:
					break

		if predictor is not None:

			if 'classifier' in predictor and predictor['classifier'] is not None:
				raw_results = {}
				for seed in race.seeds:
					raw_result = predictor['classifier'].predict(numpy.array(seed.normalized_data).reshape(1, -1))[0]
					if raw_result is not None:
						if not raw_result in raw_results:
							raw_results[raw_result] = []
						raw_results[raw_result].append(seed.runner['number'])
				for key in sorted(raw_results.keys()):
					if prediction['results'] is None:
						prediction['results'] = []
					prediction['results'].append(sorted([number for number in raw_results[key]]))

			if 'score' in predictor:
				prediction['score'] = predictor['score']

			if 'train_seeds' in predictor:
				prediction['train_seeds'] = predictor['train_seeds']

			if 'test_seeds' in predictor:
				prediction['test_seeds'] = predictor['test_seeds']
		
		return prediction

	@classmethod
	def initialize(cls):
		"""Initialize class dependencies"""

		def handle_deleting_race(race):
			for prediction in cls.find({'race_id': race['_id']}):
				prediction.delete()

		cls.event_manager.add_subscriber('deleting_race', handle_deleting_race)

		cls.create_index([('race_id', 1), ('earliest_date', 1), ('prediction_version', 1), ('seed_version', 1)])

		pyracing.Race.create_index([('entry_conditions', 1), ('track_condition', 1), ('start_time', -1)])

		@property
		def prediction(self):
			"""Return the prediction for this race"""

			if not 'prediction' in self.cache:
				self.cache['prediction'] = Prediction.get_prediction_by_race(self)
			return self.cache['prediction']

		pyracing.Race.prediction = prediction

	def __str__(self):

		return 'prediction for race {race}'.format(race=self.race)

	@property
	def confidence(self):
		"""Return the prediction score multiplied by the number of test seeds"""

		if 'score' in self and self['score'] is not None:
			if 'test_seeds' in self and self['test_seeds'] is not None:
				return self['score'] * self['test_seeds']

	@property
	def race(self):
		"""Return the race to which this prediction applies"""

		if not 'race' in self.cache:
			self.cache['race'] = pyracing.Race.get_race_by_id(self['race_id'])
		return self.cache['race']


class PredictProcessor(CommandLineProcessor):
	"""Populate the database with predictions for all runners in the specified date range"""

	def __init__(self, csv_writer, *args, **kwargs):
		"""Initialize instance dependencies"""

		super().__init__(message_prefix='predicting', *args, **kwargs)

		self.csv_writer = csv_writer

	def pre_process_date(self, date):
		"""Handle the pre_process_date event by clearing the predictor cache"""

		Prediction.clear_predictor_cache()

	def post_process_race(self, race):
		"""Handle the post_process_race event by creating a prediction for the race"""
		
		if race.prediction is not None:

			picks = [None for pick_count in range(4)]
			if 'results' in race.prediction and race.prediction['results'] is not None:
				total_picks = 0
				for result in race.prediction['results']:
					if total_picks < 4:
						picks[total_picks] = result
						total_picks += len(result)
					else:
						break
			
			row = [
				race.meet['date'].date(),
				race.meet['track'],
				race['number'],
				race['start_time'].time()
				]
			for pick in picks:
				if pick is None or len(pick) < 1:
					row.append(None)
				else:
					row.append(','.join([str(value) for value in pick]))
			row.append(race.prediction.confidence)

			self.csv_writer.writerow(row)


def main():
	"""Main entry point for the scrape console script"""

	locale.setlocale(locale.LC_ALL, '')

	configuration = PredictProcessor.get_configuration(sys.argv[1:])

	queued_csv_writer = QueuedCsvWriter(sys.stdout)
	queued_csv_writer.writerow([
		'Date',
		'Track',
		'Race',
		'Start Time',
		'1st',
		'2nd',
		'3rd',
		'4th',
		'Confidence'
		])

	processor = PredictProcessor(csv_writer=queued_csv_writer, **configuration)
	processor.process_dates(date_from=configuration['date_from'], date_to=configuration['date_to'])

	if queued_csv_writer.is_running:
		queued_csv_writer.join()


if __name__ == '__main__':
	main()