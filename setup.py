# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = 'Plumbum',
    version = '0.1.dev1',
    author = 'Augusto Roccasalva',
    author_email = 'augustoroccasalva@gmail.com',
    description = 'Simple and extensible application framework to work with Flask',
    platforms = 'any',
    license = 'BSD', # ?? this is correct

    packages = find_packages(exclude=['tests']),
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'Flask',
        'Flask-SQLAlchemy',
        'flask-wtf',
        'wtforms-alchemy',
    ],
    # TODO: Add classifiers
)
