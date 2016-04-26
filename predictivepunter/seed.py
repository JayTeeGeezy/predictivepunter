import locale
import sys

import pyracing

try:
	from .common import CommandLineProcessor
except SystemError:
	from common import CommandLineProcessor


class Seed(pyracing.Entity):
	"""A seed represents a runner's data in a consistent format applicable to machine learning"""

	SEED_VERSION = 1

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

		for key in ('barrier', 'number', 'weight'):
			seed['raw_data'].append(runner[key])
		for key in ('age', 'carrying', 'spell', 'up'):
			seed['raw_data'].append(getattr(runner, key))
		for key in ('average_prize_money', 'average_starting_price', 'roi'):
			seed['raw_data'].append(getattr(runner.career, key))
		for key1 in ('at_distance', 'at_distance_on_track', 'career' ,'firm', 'good', 'heavy', 'on_track', 'on_up', 'since_rest', 'soft', 'synthetic', 'with_jockey'):
			performance_list = getattr(runner, key1)
			for key2 in ('average_momentum', 'fourth_pct', 'maximum_momentum', 'minimum_momentum', 'second_pct', 'starts', 'third_pct', 'win_pct'):
				seed['raw_data'].append(getattr(performance_list, key2))

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