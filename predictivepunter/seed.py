import locale
import sys

import pyracing

try:
	from .common import CommandLineProcessor
except SystemError:
	from common import CommandLineProcessor


class Seed(pyracing.Entity):
	"""A seed represents a runner's data in a consistent format applicable to machine learning"""

	SEED_VERSION = 2

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
			'raw_data':		[]
		}

		for key in ('number', 'barrier', 'weight'):
			seed['raw_data'].append(runner[key])
		for key in ('carrying', 'age', 'spell', 'up'):
			seed['raw_data'].append(getattr(runner, key))
		for key in ('average_prize_money', 'average_starting_price', 'roi'):
			seed['raw_data'].append(getattr(runner.career, key))
		for key1 in ('at_distance', 'at_distance_on_track', 'career' ,'firm', 'good', 'heavy', 'on_track', 'on_up', 'since_rest', 'soft', 'synthetic', 'with_jockey'):
			performance_list = getattr(runner, key1)
			for key2 in ('starts', 'win_pct', 'place_pct', 'second_pct', 'third_pct', 'fourth_pct'):
				seed['raw_data'].append(getattr(performance_list, key2))
			seed['raw_data'].extend(runner.calculate_expected_speed(key1))

		return seed

	@classmethod
	def initialize(cls):
		"""Initialize class dependencies"""

		def handle_deleting_runner(runner):
			for seed in cls.find({'runner_id': runner['_id']}):
				seed.delete()

		cls.event_manager.add_subscriber('deleting_runner', handle_deleting_runner)

		cls.create_index([('runner_id', 1), ('seed_version', 1)])

	def __str__(self):

		return 'seed for runner {runner}'.format(runner=self.runner)

	@property
	def normalized_data(self):
		"""Return an array of the raw data values normalized for all runners in the race"""

		if not 'normalized_data' in self.cache:
			self.cache['normalized_data'] = [0.5 for index in range(len(self['raw_data']))]

			all_seeds = [Seed.get_seed_by_runner(runner) for runner in self.runner.race.runners]
			for index in range(len(self['raw_data'])):
				all_values = [seed['raw_data'][index] for seed in all_seeds if seed['raw_data'][index] is not None]
				if len(all_values) > 0 and max(all_values) > min(all_values):
					own_value = self['raw_data'][index]
					if own_value is None:
						average_value = sum(all_values) / len(all_values)
						self.cache['normalized_data'][index] = (average_value - min(all_values)) / (max(all_values) - min(all_values))
					else:
						self.cache['normalized_data'][index] = (own_value - min(all_values)) / (max(all_values) - min(all_values))

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

		Seed.initialize()
		pyracing.add_subscriber('saved_seed', self.handle_saved_event)

	def post_process_race(self, race):
		"""Handle the post_process_race event by creating seeds for all the runners in the race"""

		for runner in race.runners:
			Seed.get_seed_by_runner(runner)


def main():
	"""Main entry point for the scrape console script"""

	locale.setlocale(locale.LC_ALL, '')

	configuration = SeedProcessor.get_configuration(sys.argv[1:])

	processor = SeedProcessor(**configuration)
	processor.process_dates(date_from=configuration['date_from'], date_to=configuration['date_to'])


if __name__ == '__main__':
	main()