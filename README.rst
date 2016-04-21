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

To use predictivepunter, you must first import the predictivepunter package into your Python interpreter as follows:

	>>> import predictivepunter


Testing
-------

To run the included test suite, execute the following command from the root directory of the predictivepunter repository::

	python setup.py test

The above command will ensure all test dependencies are installed in your current Python environment. For more concise output during subsequent test runs, the following command can be executed from the root directory of the predictivepunter repository instead::

	nosetests
