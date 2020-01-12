#!/usr/bin/python3
# pylint: disable=missing-docstring
import os
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
    README = f.read()

setup(
    name='cobib',
    version='1.0.0',
    description='Console Reference Manager',
    long_description=README,
    long_description_content_type='text/markdown',
    keywords='console reference manager',
    url='https://gitlab.com/mrossinek/cobib',
    license='MIT',
    author='Max Rossmannek',
    author_email='rmax@ethz.ch',
    platforms=['any'],
    packages=['cobib'],
    package_data={'cobib': ['docs/default.ini']},
    python_requires='>=3.5',
    install_requires=[
        'bibtexparser',
        'bs4',
        'pdftotext',
        'requests',
        'ruamel.yaml',
        'tabulate'
    ],
    entry_points={
        'console_scripts': [
            'cobib = cobib.__main__:main'
        ]
    }
)
