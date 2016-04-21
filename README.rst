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


Testing
-------

To run the included test suite, execute the following command from the root directory of the predictivepunter repository::

	python setup.py test

The above command will ensure all test dependencies are installed in your current Python environment. For more concise output during subsequent test runs, the following command can be executed from the root directory of the predictivepunter repository instead::

	nosetests

Alternatively, individual components of pyracing can be tested by executing any of the following commands from the root directory of the pyracing repository::

	nosetests predictivepunter.test.scrape


Version History
---------------

0.1.0 (21 April 2016)
	Interim release to facilitate database pre-population
