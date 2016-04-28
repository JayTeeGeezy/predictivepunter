from setuptools import setup


def read_text(filename):
	with open(filename) as f:
		return f.read()


setup(
	name='predictivepunter',
	version='0.3.0',
	description='Applying predictive analytics to horse racing via Python',
	long_description=read_text('README.rst'),
	classifiers=[
		'Development Status :: 2 - Pre-Alpha',
		'Environment :: Console',
		'Intended Audience :: End Users/Desktop',
		'License :: OSI Approved :: MIT License',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3.4',
		'Topic :: Scientific/Engineering :: Information Analysis'
	],
	keywords='predictive analytics horse racing',
	url='https://github.com/JayTeeGeezy/predictivepunter',
	author='Jason Green',
	author_email='JayTeeGeezy@outlook.com',
	license='MIT',
	packages=[
		'predictivepunter'
	],
	scripts=[
	],
	entry_points={
		'console_scripts': [
			'scrape=predictivepunter.scrape:main',
			'seed=predictivepunter.seed:main',
			'predict=predictivepunter.predict:main'
		]
	},
	install_requires=[
		'cache_requests',
		'jtgpy',
		'lxml',
		'numpy',
		'pymongo',
		'pypunters',
		'pyracing',
		'scikit-learn',
		'scipy'
	],
	test_suite='nose.collector',
	tests_require=[
		'cache_requests',
		'jtgpy',
		'lxml',
		'nose',
		'numpy',
		'pymongo',
		'pypunters',
		'pyracing',
		'scikit-learn',
		'scipy'
	],
	dependency_links=[
	],
	include_package_data=True,
	zip_safe=False
	)