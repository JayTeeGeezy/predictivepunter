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

Valid options for the scrape command-line utility are documented in the table below:

+----------------------+-------------------------------+-----------------------------------+
| Short Format         | Long Format                   | Default                           |
+======================+===============================+===================================+
| -b                   | --backup-database             | False                             |
+----------------------+-------------------------------+-----------------------------------+
| -d date_from-date_to | --date=date_from-date_to      | datetime.today()-datetime.today() |
+----------------------+-------------------------------+-----------------------------------+
| -n database_name     | --database_name=database_name | predictivepunter                  |
+----------------------+-------------------------------+-----------------------------------+
| -q                   | --quiet                       | False                             |
+----------------------+-------------------------------+-----------------------------------+
| -t threads           | --threads=4                   | 4                                 |
+----------------------+-------------------------------+-----------------------------------+
| -v                   | --verbose                     | False                             |
+----------------------+-------------------------------+-----------------------------------+
| -x cache_expiry      | --cache_expiry=cache_expiry   | 600 (10 minutes)                  |
+----------------------+-------------------------------+-----------------------------------+


Testing
-------

To run the included test suite, execute the following command from the root directory of the predictivepunter repository::

	python setup.py test

The above command will ensure all test dependencies are installed in your current Python environment. For more concise output during subsequent test runs, the following command can be executed from the root directory of the predictivepunter repository instead::

	nosetests

Alternatively, individual components of pyracing can be tested by executing any of the following commands from the root directory of the pyracing repository::

	nosetests predictivepunter.test.scrape
