predictivepunter
================

Applying predictive analytics to horse racing via Python


Installation
------------

To install the latest release of predictivepunter to your current Python environment, execute the following command::

	pip install predictivepunter

Alternatively, to install predictivepunter from a source distribution, execute the following command from the root directory of the predictivepunter repository::

	python setup.py install

To install predictivepunter from a source distribution as a symlink for development purposes, execute the following command from the root directory of the predictivepunter repository instead::

	python setup.py develop


Usage
-----

Before using predictivepunter to predict the results of future races, a local database must be populated with historical racing data. To pre-populate the database, a 'scrape' command-line utility is made available to any Python environment in which predictivepunter is installed, and can be called with the following command line::

	scrape <options>

Valid options for the scrape command-line utility are documented below:

-b, --backup-database             Dump the database to the filesystem after scraping each day's data (default: False)
-d from-to, --date=from-to        The range of dates to scrape (default: today-today)
-n name, --database-name=name     The name of the database to use (default: predictivepunter)
-q, --quiet                       Suppress progress log messages (default: False)
-t threads, --threads=threads     The number of threads to use (default: 4)
-v, --verbose                     Output debugging log messages (default: False)
-x expiry, --cache-expiry=expiry  The HTTP cache timeout period in seconds (default: 600)

With a local database of historical racing data populated, the next step is to pre-seed query data for each of the runners stored in the database. To pre-seed query data, a 'seed' command-line utility is made available to any Python environment in which predictivepunter is installed, and can be called with the following command line::

	seed <options>

Valid options for the seed command-line utility are the same as those documented for the scrape command-line utility above.

With query data seeded in the database, predictions can be made using the predict command-line utility as follows::

	predict <options>

Valid options for the predict command-line utility are the same as those documented for the scrape command-line utility above.

The predict command-line utility will produce a CSV-formatted list on sys.stdout, of predictions for all races in the specified date range.


Testing
-------

To run the included test suite, execute the following command from the root directory of the predictivepunter repository::

	python setup.py test

The above command will ensure all test dependencies are installed in your current Python environment. For more concise output during subsequent test runs, the following command can be executed from the root directory of the predictivepunter repository instead::

	nosetests

Alternatively, individual components of pyracing can be tested by executing any of the following commands from the root directory of the pyracing repository::

	nosetests predictivepunter.test.scrape
	nosetests predictivepunter.test.seed
	nosetests predictivepunter.test.predict


Version History
---------------

0.2.3 (27 April 2016)
	Fix ZeroDivisionErrors

0.2.2 (27 April 2016)
	Fix ValueErrors in generate_seed

0.2.1 (26 April 2016)
	Fix memory leak and schema when seeding query data

0.2.0 (26 April 2016)
	Interim release to facilitate pre-seeding query data

0.1.1 (22 April 2016)
	Fix exceptions in pypunters and pyracing

0.1.0 (21 April 2016)
	Interim release to facilitate database pre-population
