# -*- coding: utf-8 -*-

from functools import reduce
from re import sub

from flask import g


def set_current_view(view):
    g._plumbum_view = view


def get_current_view():
    return getattr(g, '_plumbum_view', None)


def prettify_class_name(name):
    return sub(r'(?<=.)([A-Z])', r' \1', name)


def recursive_getattr(obj, attr, default=None):
    """
    Recursive getattr.

    :param attr:
        Dot delimited attribute name
    :param default:
        Default value

    Example::

        recursive_getattr(obj, 'a.b.c')
    """
    try:
        return reduce(getattr, attr.split('.'), obj)
    except AttributeError:
        return default


def is_running_main():
    import os
    return os.environ.get('WERKZEUG_RUN_MAIN', False)
