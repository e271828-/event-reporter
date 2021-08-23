#! /usr/bin/env python
from setuptools import setup

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='event-reporter',
    author='e271828-',
    author_email='e271828-@users.noreply.github.com',
    url='https://github.com/e271828-/event-reporter',
    description='backend reporting via a worker/queue system',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='BSD',
    version='1.1.0',
    packages=['event_reporter'],
    install_requires=['honeycomb-beeline>=2.1.0', 'google_measurement_protocol>=1.0', 'typing>=3.6.0;python_version<"3.5"', 'requests>=2.22.0'],
    test_requires=['fakeredis','nose'],
    classifiers=CLASSIFIERS,
    platforms=['any'])
