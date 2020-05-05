#!/usr/bin/python3
# pylint: disable=missing-docstring
import os
import re
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.md'), 'r', encoding='utf-8') as f:
    README = f.read()
with open(os.path.join(HERE, 'cobib/__init__.py'), 'r') as f:
    VERSION = re.search(r"__version__ = '([\S]+)'", f.read()).group(1)

setup(
    name='cobib',
    version=VERSION,
    description='Console Bibliography',
    long_description=README,
    long_description_content_type='text/markdown',
    keywords='reference-manager terminal-based console-based citation-manager bibtex doi arxiv cli \
              command-line bibliography',
    url='https://gitlab.com/mrossinek/cobib',
    license='MIT',
    author='Max Rossmannek',
    author_email='rmax@ethz.ch',
    platforms=['any'],
    packages=['cobib'],
    package_data={'cobib': ['docs/default.ini', 'commands/*', 'tui/*']},
    python_requires='>=3.5',
    install_requires=[
        'bibtexparser',
        'beautifulsoup4',
        'pylatexenc',
        'requests',
        'ruamel.yaml',
    ],
    entry_points={
        'console_scripts': [
            'cobib = cobib.__main__:main'
        ]
    }
)
