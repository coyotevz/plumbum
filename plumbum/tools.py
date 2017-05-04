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


def run_scss(infile, outfile):
    import subprocess, atexit

    print('Compiling {} > {}'.format(infile, outfile))
    proc = subprocess.Popen(['/usr/bin/sass', '--watch', '{}:{}'.format(infile, outfile)])
    atexit.register(proc.kill)


def is_running_main():
    import os
    return os.environ.get('WERKZEUG_RUN_MAIN', False)
