import locale
import sys

import pyracing

try:
	from .common import CommandLineProcessor
except SystemError:
	from common import CommandLineProcessor


class Seed(pyracing.Entity):
	"""A seed represents a runner's data in a consistent format applicable to machine learning"""

	SEED_VERSION = 4

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
			seed['raw_data'].append(getattr(runner.jockey_career, key))
		for key1 in ('at_distance', 'at_distance_on_track', 'career' ,'firm', 'good', 'heavy', 'on_track', 'on_up', 'since_rest', 'soft', 'synthetic', 'with_jockey', 'jockey_at_distance', 'jockey_at_distance_on_track', 'jockey_career', 'jockey_firm', 'jockey_good', 'jockey_heavy', 'jockey_on_track', 'jockey_soft', 'jockey_synthetic'):
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

		@property
		def seeds(self):
			"""Return a list of seeds for all runners in a race"""

			if 'seeds' not in self.cache:
				self.cache['seeds'] = [Seed.get_seed_by_runner(runner) for runner in self.runners]
			return self.cache['seeds']

		pyracing.Race.seeds = seeds

	def __str__(self):

		return 'seed for runner {runner}'.format(runner=self.runner)

	@property
	def normalized_data(self):
		"""Return an array of the raw data values normalized for all runners in the race"""

		if not 'normalized_data' in self:
			
			self['normalized_data'] = [0.5 for item in self['raw_data']]

			for index in range(len(self['raw_data'])):
				all_values = [seed['raw_data'][index] for seed in self.runner.race.seeds if seed['raw_data'][index] is not None]
				if len(all_values) > 0 and max(all_values) > min(all_values):
					own_value = self['raw_data'][index]
					if own_value is None:
						average_value = sum(all_values) / len(all_values)
						self['normalized_data'][index] = (average_value - min(all_values)) / (max(all_values) - min(all_values))
					else:
						self['normalized_data'][index] = (own_value - min(all_values)) / (max(all_values) - min(all_values))

			self.save()

		return self['normalized_data']

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

	def post_process_race(self, race):
		"""Handle the post_process_race event by creating and normalizing seed data for the race's runners"""

		for seed in race.seeds:
			seed.normalized_data


def main():
	"""Main entry point for the scrape console script"""

	locale.setlocale(locale.LC_ALL, '')

	configuration = SeedProcessor.get_configuration(sys.argv[1:])

	processor = SeedProcessor(**configuration)
	processor.process_dates(date_from=configuration['date_from'], date_to=configuration['date_to'])


if __name__ == '__main__':
	main()