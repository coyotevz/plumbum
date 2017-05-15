# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
try:
    from babel.messages import frontend as babel
    cmdclass = {
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog,
    }

except ImportError:
    cmdclass = {}

setup(
    name='Plumbum',
    version='0.1.dev1',
    author='Augusto Roccasalva',
    author_email='augustoroccasalva@gmail.com',
    description='Simple and extensible application framework for Flask',
    platforms='any',
    license='BSD',  # ?? this is correct
    cmdclass=cmdclass,

    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'Flask-SQLAlchemy',
        'Flask-BabelEx',
        'flask-wtf',
        'wtforms-alchemy',
        'flask-webpack',
    ],
    # TODO: Add classifiers
)
