import locale
import logging
import sys
from threading import RLock

import pyracing
from sklearn import preprocessing

try:
	from .common import CommandLineProcessor
except SystemError:
	from common import CommandLineProcessor


class Seed(pyracing.Entity):
	"""A seed represents a runner's data in a consistent format applicable to machine learning"""

	SEED_VERSION = 5

	jockey_seed_cache = {}
	jockey_seed_cache_lock = RLock()

	@classmethod
	def delete_expired(cls, *args, **kwargs):
		"""Delete outdated seeds"""

		cls.get_database_collection().delete_many({'seed_version': {'$lt': cls.SEED_VERSION}})

	@classmethod
	def get_seed_by_id(cls, id):
		"""Get the single seed with the specified database ID"""

		return cls.find_one({'_id': id})

	@classmethod
	def get_seed_by_runner(cls, runner):
		"""Get the seed for the specified runner"""

		return cls.find_or_scrape_one(
			filter={'runner_id': runner['_id'], 'seed_version': cls.SEED_VERSION},
			scrape=cls.generate_seed,
			scrape_args=[runner],
			expiry_date=None
			)

	@classmethod
	def generate_seed(cls, runner):
		"""Generate a seed for the specified runner"""
		
		seed = {
			'runner_id':	runner['_id'],
			'seed_version':	cls.SEED_VERSION,
			'result':		runner.result,
			'raw_data':		[]
		}

		for key in ('number', 'barrier', 'weight'):
			seed['raw_data'].append(runner[key])
		for key in ('carrying', 'age', 'spell', 'up'):
			seed['raw_data'].append(getattr(runner, key))
		for key in ('average_prize_money', 'average_starting_price', 'roi'):
			seed['raw_data'].append(getattr(runner.career, key))
		for key1 in ('at_distance', 'at_distance_on_track', 'career' ,'firm', 'good', 'heavy', 'on_track', 'on_up', 'since_rest', 'soft', 'synthetic', 'with_jockey', 'jockey_at_distance', 'jockey_at_distance_on_track', 'jockey_on_track'):
			performance_list = getattr(runner, key1)
			for key2 in ('starts', 'win_pct', 'place_pct', 'second_pct', 'third_pct', 'fourth_pct'):
				seed['raw_data'].append(getattr(performance_list, key2))
			seed['raw_data'].extend(runner.calculate_expected_speed(key1))
		seed['raw_data'].extend(cls.get_jockey_seed(runner))

		return seed

	@classmethod
	def get_jockey_seed(cls, runner):
		"""Retrieve seed data for the specified runner's jockey from the cache, or generate it"""

		if runner is not None and runner.jockey is not None:
			with cls.jockey_seed_cache_lock:
				key = (runner.jockey['_id'], runner.race.meet['date'])
				if not key in cls.jockey_seed_cache:
					cls.jockey_seed_cache[key] = []
					for key1 in ('average_prize_money', 'average_starting_price', 'roi'):
						cls.jockey_seed_cache[key].append(getattr(runner.jockey_career, key1))
					for key1 in ('jockey_career', 'jockey_firm', 'jockey_good', 'jockey_heavy', 'jockey_soft', 'jockey_synthetic'):
						performance_list = getattr(runner, key1)
						for key2 in ('starts', 'win_pct', 'place_pct', 'second_pct', 'third_pct', 'fourth_pct'):
							cls.jockey_seed_cache[key].append(getattr(performance_list, key2))
						cls.jockey_seed_cache[key].extend(runner.calculate_expected_speed(key1))
				return cls.jockey_seed_cache[key]
		else:
			values = []
			for key1 in ('average_prize_money', 'average_starting_price', 'roi'):
				values.append(None)
			for key1 in ('jockey_career', 'jockey_firm', 'jockey_good', 'jockey_heavy', 'jockey_soft', 'jockey_synthetic'):
				for key2 in ('starts', 'win_pct', 'place_pct', 'second_pct', 'third_pct', 'fourth_pct'):
					values.append(None)
				values.extend([None, None, None])
			return values

	@classmethod
	def initialize(cls):
		"""Initialize class dependencies"""

		def handle_deleting_runner(runner):
			for seed in cls.find({'runner_id': runner['_id']}):
				seed.delete()

		cls.event_manager.add_subscriber('deleting_runner', handle_deleting_runner)

		cls.create_index([('seed_version', 1)])
		cls.create_index([('runner_id', 1), ('seed_version', 1)])

		@property
		def seed(self):
			"""Return the seed for the runner"""

			if 'seed' not in self.cache:
				self.cache['seed'] = Seed.get_seed_by_runner(self)
			return self.cache['seed']

		pyracing.Runner.seed = seed

		@property
		def seeds(self):
			"""Return a list of seeds for all runners in a race"""

			if 'seeds' not in self.cache:
				self.cache['seeds'] = [runner.seed for runner in self.runners]
			return self.cache['seeds']

		pyracing.Race.seeds = seeds

	def __str__(self):

		return 'seed for runner {runner}'.format(runner=self.runner)

	@property
	def fixed_data(self):
		"""Return a list of seed values with missing values set to the average of the same value for other seeds"""

		if 'fixed_data' not in self:
			self['fixed_data'] = list(self['raw_data'])
			if len([value for value in self['fixed_data'] if value is None]) > 0:
				self['fixed_data'] = [0.5 for item in self['raw_data']]
				all_values = [seed['raw_data'] for seed in self.runner.race.seeds]
				for index in range(len(self['raw_data'])):
					if self['raw_data'][index] is None:
						other_values = [seed[index] for seed in all_values if seed[index] is not None]
						if len(other_values) > 0:
							self['fixed_data'][index] = sum(other_values) / len(other_values)
					else:
						self['fixed_data'][index] = self['raw_data'][index]
			self.save()
		return self['fixed_data']

	@property
	def normalized_data(self):
		"""Return a list of seed values with values normalized against the same value for other seeds in the same race"""

		if 'normalized_data' not in self.cache:
			all_seeds = [self.fixed_data] + [seed.fixed_data for seed in self.runner.race.seeds if seed['_id'] != self['_id']]
			normalized_seeds = preprocessing.normalize(all_seeds, axis=0)
			self.cache['normalized_data'] = normalized_seeds[0]
		return self.cache['normalized_data']

	@property
	def runner(self):
		"""Return the runner to which this seed applies"""

		if not 'runner' in self.cache:
			self.cache['runner'] = pyracing.Runner.get_runner_by_id(self['runner_id'])
		return self.cache['runner']


class SeedProcessor(CommandLineProcessor):
	"""Seed the database with query data for all runners in the specified date range"""

	def __init__(self, *args, **kwargs):
		"""Initialize instance dependencies"""

		super().__init__(message_prefix='seeding', *args, **kwargs)

	def pre_process_date(self, date):
		"""Handle the pre_process_date event by clearing the jockey_seed_cache"""

		for key in Seed.jockey_seed_cache:
			del Seed.jockey_seed_cache[key]

	def post_process_runner(self, runner):
		"""Handle the post_process_runner event by creating a seed for the runner and fixing its data"""

		runner.seed


def main():
	"""Main entry point for the scrape console script"""

	locale.setlocale(locale.LC_ALL, '')

	configuration = SeedProcessor.get_configuration(sys.argv[1:])

	processor = SeedProcessor(**configuration)
	processor.process_dates(date_from=configuration['date_from'], date_to=configuration['date_to'])


if __name__ == '__main__':
	main()