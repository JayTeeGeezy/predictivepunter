import locale
import sys

try:
	from .common import CommandLineProcessor
except SystemError:
	from common import CommandLineProcessor


class ScrapeProcessor(CommandLineProcessor):
	"""Scrape all racing data for a specified date range"""

	def __init__(self, *args, **kwargs):
		"""Initialize instance dependencies"""

		self.pre_process_date = self.pre_process_meet = self.pre_process_race = self.pre_process_runner = self.pre_process_horse = self.do_nothing
		self.post_process_meet = self.post_process_race = self.post_process_runner = self.post_process_horse = self.do_nothing
		self.process_jockey = self.process_trainer = self.process_performance = self.do_nothing

		super().__init__(message_prefix='scraping', *args, **kwargs)

	def do_nothing(self, item):
		pass


def main():
	"""Main entry point for the scrape console script"""

	locale.setlocale(locale.LC_ALL, '')

	configuration = ScrapeProcessor.get_configuration(sys.argv[1:])

	processor = ScrapeProcessor(**configuration)
	processor.process_dates(date_from=configuration['date_from'], date_to=configuration['date_to'])


if __name__ == '__main__':
	main()