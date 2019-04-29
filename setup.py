from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='crema',
    version='1.0.0',
    description='Console Reference Manager',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='console reference manager',
    url='https://github.com/mrossinek/crema',
    license='MIT',
    author='Max Rossmannek',
    author_email='rmax@ethz.ch',
    platforms=['any'],
    py_modules=['crema'],
    python_requires='>=3.5',
    install_requires=[
        'bs4',
        'pdftotext',
        'requests',
        'tabulate'
    ]
)
