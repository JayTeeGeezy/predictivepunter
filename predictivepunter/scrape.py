import pyracing


def do_nothing(item):
	pass

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