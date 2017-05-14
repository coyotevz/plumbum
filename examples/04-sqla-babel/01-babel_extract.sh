#!/bin/sh
pybabel extract -F ../../babel.cfg -k _ -k lazy_gettext -o locales/sqla-babel.pot .
