# -*- coding: utf-8 -*-

from functools import reduce

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
