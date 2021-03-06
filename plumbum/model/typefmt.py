# -*- coding: utf-8 -*-

from enum import Enum
import json

from jinja2 import Markup


def null_formatter(view, value):
    """
    Return `NULL` as the string for `None` value

    :param value:
        Value to check
    """
    return Markup('<i>NULL</i>')


def empty_formatter(view, value):
    """
    Return empty string for `None` value

    :param value:
        Value to check
    """
    return ''


def bool_formatter(view, value):
    """
    Return check icon if value is `True` or empty string otherwise.

    :param value:
        Value to check
    """
    glyph = 'ok-circle' if value else 'minus-sign'
    fa = 'check-circle' if value else 'minus-circle'
    return Markup('<span class="fa fa-{} glyphicon glyphicon-{} icon-{}">'
                  '</span>'.format(fa, glyph, glyph))


def list_formatter(view, values):
    """
    Return string with comma separated values

    :param values:
        Value to check
    """
    return ', '.join(v for v in values)


def dict_formatter(view, value):
    """
    Removes unicode entitties when displaying dict as string. Also unescapes
    non-ASCII characters stored in JSON.

    :param value:
        Dict to convert to string
    """
    return json.dumps(value, ensure_ascii=True)


def enum_formatter(view, value):
    """
    Return the name of the enumerated member.

    :param value:
        Value to check
    """
    return value.name


BASE_FORMATTERS = {
    type(None): empty_formatter,
    bool: bool_formatter,
    list: list_formatter,
    dict: dict_formatter,
    Enum: enum_formatter,
}

EXPORT_FORMATTERS = {
    type(None): empty_formatter,
    list: list_formatter,
    dict: dict_formatter,
    Enum: enum_formatter,
}
