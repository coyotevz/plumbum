# -*- coding: utf-8 -*-

import warnings

from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY

from ..tools import recursive_getattr


def get_field_value(model, name):
    return recursive_getattr(model, name)


def column_name(field):
    return field.replace('_', ' ').title()


def column_names(model, only_columns=None, excluded_columns=None,
                 display_all_relations=False, display_pk=False):
    """
    Return a list of tuples with the model field name and formatted field name.
    """

    if not only_columns:
        only_columns = list_columns(model, display_all_relations, display_pk)

    if excluded_columns:
        only_columns = [c for c in only_columns if c not in excluded_columns]

    formatted_columns = []
    for c in only_columns:
        try:
            column, path = get_field_with_path(model, c)

            if path:
                col_name = c
            else:
                if getattr(column, 'key', None) is not None:
                    col_name = column.key
                else:
                    col_name = c
        except AttributeError:
            col_name = c

        visible_name = column_name(col_name)

        formatted_columns.append((col_name, visible_name))

    return formatted_columns


def list_columns(model, display_all_relations=False, display_pk=False):
    "Return a list fo columns from the model."
    columns = []

    for prop in class_mapper(model).iterate_properties:
        if hasattr(prop, 'direction'):
            if display_all_relations or prop.direction.name == 'MANYTOONE':
                columns.append(prop.key)
        elif hasattr(prop, 'columns'):
            if len(prop.columns) > 1:
                filtered = list(filter(lambda c: c.table == model.__table__,
                                       columns))
                if len(filtered) > 1:
                    warnings.warn("Can not convert multiple-column properties "
                                  "({}.{})".format(model, prop.key))
                    continue
                column = filtered[0]
            else:
                column = prop.columns[0]

            if column.foreign_keys:
                continue
            if not display_pk and column.primary_key:
                continue
            columns.append(prop.key)

    return columns


def sortable_columns(model, display_pk=False):
    "Return a dictionary of sortable columns."
    columns = dict()

    for prop in class_mapper(model).iterate_properties:
        if hasattr(prop, 'columns'):
            # Sanity check
            if len(prop.columns) > 1:
                # Multi-column properties are not supported
                continue

            column = prop.columns[0]

            # Can't sort on primary or foreign keys by default
            if column.foreign_keys:
                continue

            if display_pk and column.primary_key:
                continue

            columns[prop.key] = column

    return columns


def get_field_with_path(model, name, return_remote_proxy_attr=True):
    "Resolve property by name and figure out its join path"
    path = []

    # For strings, resolve path
    if isinstance(name, str):
        current_model = model

        value = None
        for attribute in name.split('.'):
            value = getattr(current_model, attribute)

            if is_association_proxy(value):
                relation_values = value.attr
                if return_remote_proxy_attr:
                    value = value.remote_attr
            else:
                relation_values = [value]

            for relation_value in relation_values:
                if is_relationship(relation_value):
                    current_model = relation_value.property.mapper.class_
                    table = current_model.__table__
                    if need_join(model, table):
                        path.append(relation_value)

        attr = value
    else:
        attr = value

        if isinstance(attr, InstrumentedAttribute) or \
                is_association_proxy(attr):
            columns = get_columns_for_field(attr)
            if len(columns) > 1:
                raise Exception('Can only handle one columm for {}'.format(
                                name))

            column = columns[0]

            if need_join(model, column.table):
                path.append(column.table)

    return attr, path


def get_columns_for_field(field):
    if (not field or
            not hasattr(field, 'property') or
            not hasattr(field.property, 'columns') or
            not field.property.columns):
        raise Exception("Invalid field {}: does not contains any columns."
                        .format(field))

    return field.property.columns


def get_primary_key(model):
    "Return primary key name from a model"
    mapper = class_mapper(model)
    pks = [mapper.get_property_by_column(c).key for c in mapper.primary_key]
    if len(pks) == 1:
        return pks[0]
    elif len(pks) > 1:
        return tuple(pks)
    else:
        return None


def need_join(model, table):
    "Check if join to a table is necessary."
    return table not in class_mapper(model).tables


def is_relationship(attr):
    return hasattr(attr, 'property') and hasattr(attr.property, 'direction')


def is_association_proxy(attr):
    return hasattr(attr, 'extension_type') and \
           attr.extension_type == ASSOCIATION_PROXY
