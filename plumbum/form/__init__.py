# -*- coding: utf-8 -*-

from wtforms.fields.core import UnboundField
from wtforms_alchemy import model_form_factory
from flask_wtf import FlaskForm


BaseForm = model_form_factory(base=FlaskForm)


def _recreate_field(unbound):
    """
    Create a new instance of the unbound field, resettings wtforms creation
    counter.
    """
    if not isinstance(unbound, UnboundField):
        raise ValueError('recreate_field expect UnboundField instance, {} was '
                         'passed.'.format(type(unbound)))

    return unbound.field_class(*unbound.args, **unbound.kwargs)


def build_form(model,
               base_class=BaseForm,
               only=None,
               exclude=None,
               field_args=None,
               hidden_pk=False,
               ignore_hidden=True,
               extra_fields=None):
    """
    Generate form from model.
    """

    meta = {
        'model': model,
        'only': only or [],
        'exclude': exclude or [],
    }

    if field_args is not None:
        meta['field_args'] = field_args

    ns = {'Meta': type('Meta', (object,), meta)}

    if not only and extra_fields:
        for name, field in extra_fields.items():
            ns[name] = _recreate_field(field)

    return type(model.__name__ + 'Form', (base_class,), ns)
