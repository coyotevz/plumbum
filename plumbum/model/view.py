# -*- coding: utf-8 -*-

import csv
import mimetypes
import time
from math import ceil
from urllib.parse import urljoin, urlparse

from sqlalchemy import func, Table
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import desc
from werkzeug import secure_filename
from flask import Response, request, redirect, flash, stream_with_context
from jinja2 import contextfunction
from wtforms.validators import ValidationError

try:
    import tablib
except ImportError:
    tablib = None

from ..base import BaseView, expose
from ..babel import gettext, lazy_gettext
from ..form import BaseForm, build_form
from ..tools import prettify_class_name
from . import tools
from . import typefmt


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc)


def get_redirect_target(param_name='url'):
    target = request.values.get(param_name)

    if target and is_safe_url(target):
        return target


class ViewArgs(object):
    """
    List view arguments
    """
    def __init__(self, page=None, page_size=None, sort=None, sort_desc=None,
                 search=None, filters=None, extra_args=None):
        self.page = page
        self.page_size = page_size
        self.sort = sort
        self.sort_desc = bool(sort_desc)
        self.search = search
        self.filters = filters
        self.extra_args = extra_args or dict()

        if not self.search:
            self.search = None

    def clone(self, **kwargs):
        if self.filters:
            filters = list(self.filters)
        else:
            filters = None

        kwargs.setdefault('page', self.page)
        kwargs.setdefault('page_size', self.page_size)
        kwargs.setdefault('sort', self.sort)
        kwargs.setdefault('sort_desc', self.sort_desc)
        kwargs.setdefault('search', self.search)
        kwargs.setdefault('filters', filters)
        kwargs.setdefault('extra_args', dict(self.extra_args))

        return ViewArgs(**kwargs)


class FilterGroup(object):

    def __init__(self, label):
        self.label = label
        self.filters = []

    def append(self, filter):
        self.filters.append(filter)


class ModelView(BaseView):
    """
    SQLAlchemy model view.
    """
    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = False

    # Templates
    list_template = 'plumbum/model/list.html'
    edit_template = 'plumbum/model/edit.html'
    create_template = 'plumbum/model/create.html'
    details_template = 'plumbum/model/details.html'

    # Modal Templates
    edit_modal_template = 'plumbum/model/modals/edit.html'
    create_modal_template = 'plumbum/model/modals/create.html'
    details_modal_template = 'plumbum/model/modals/details.html'

    # Modals
    edit_modal = False
    create_modal = False
    details_modal = False

    # Labels & tooltips
    create_label = lazy_gettext('Create')
    create_tooltip = lazy_gettext('Create New Record')
    edit_label = lazy_gettext('Edit')
    edit_tooltip = lazy_gettext('Edit Record')
    delete_label = lazy_gettext('Delete')
    delete_tooltip = lazy_gettext('Delete Record')

    # Customizations
    column_list = None
    """
    Collection of the model field names for the list view.
    If set to `None`, will get them from the model.

    For example::

        class MyModelView(ModelView):
            column_list = ('name', 'last_name', 'email')

    SQLAlchemy model attributes can be used instead of strings::

        class MyModelView(ModelView):
            column_list = ('name', User.last_name)

    When using SQLAlchemy models, you can reference related columns like this::

        class MyModelView(ModelView):
            column_list = ('<relationship>.<related column name>')
    """

    column_exclude_list = None
    """
    Collection of excluded list column names.

    For example::

        class MyModelView(ModelView):
            column_exclude_list = ('last_name', 'email')
    """

    column_details_list = None
    """
    Collection of the field names included in the details view.
    """

    column_details_exclude_list = None
    """
    Collection of fields excluded from the details view.
    """

    column_export_list = None
    """
    Collection of the field names included in the export.
    """

    column_export_exclude_list = None
    """
    Collection of fields excluded for the export.
    """

    column_choices = None
    """
    Map choices to columns in list view
    """

    column_display_pk = False
    """
    Controls if the primary key should be displayed in the list view.
    """

    column_display_all_relations = False
    """
    Controls if list view should display all relations, not only many-to-one.
    """

    column_formatters = dict()
    """
    Dictionary of list view columns formatters.
    """

    column_formatters_export = None
    """
    Dictionary of list view column formatters to be used for export.
    """

    column_type_formatters = None
    """
    Dictionary of value type formatters to be used in the list view.
    """

    column_type_formatters_export = None
    """
    Dictionary of value type formatters to be used in the export.
    """

    column_labels = None
    """
    Dictionary where key is a column name and value is string to display.
    """

    column_descriptions = None
    """
    Dictionary where keys is column name and value is description.
    """

    column_sortable_list = None
    """
    Collection of the sortable columns for the list view.
    """

    column_default_sort = None
    """
    Default sort column if no sorting is applied.
    """

    column_details_link = None
    """
    Index or name of column where put link to details/edit view.
    """

    # Form settings
    form = None
    """
    Form class. Override if yo want to use custom form for your model
    """

    form_base_class = BaseForm
    """
    Base form class. Will be used by form scaffolding function when creating
    model form.
    """

    field_args = None
    """
    Dictionary of form field arguments. Refer to WTForms documentation.
    """

    form_columns = None
    """
    Collection of model field names for the form. If set to `None` will get
    them from the model.
    """

    form_excluded_columns = None
    """
    Collection of excluded form field names.
    """

    form_overrides = None
    """
    Dictionary of form column overrides.
    """

    form_widget_args = None
    """
    Dictionary of form widget rendering arguments.
    """

    form_choices = None
    """
    Map choices to form fields
    """

    form_extra_fields = None
    """
    Dictionary of additional fields.
    """

    form_rules = None
    """
    List of rendering rules for model creation form.
    """

    form_edit_rules = None
    """
    Customized rules for the edit form.
    """

    form_create_rules = None
    """
    Customized rule for the create form.
    """

    # Export settings
    export_max_rows = 0
    """
    Maximum number of rows allowed for export.
    """

    export_types = ['csv']
    """
    A list of available export filetypes. `csv` only is default. Check tablib.
    """

    # Pagination settings
    page_size = 20
    """
    Default page size for pagination.
    """

    can_set_page_size = False
    """
    Allow to select page size via dropdown list
    """

    simple_pager = False
    """
    Enable or disable simple list pager (only show prev/next buttons).
    """

    ignore_hidden = True
    """
    Ignore field that starts with "_"
    """

    def __init__(self, model, session, name=None, endpoint=None, url=None,
                 static_folder=None):
        self.model = model
        self.session = session

        # If name not provided, it is model name
        if name is None and self.name is None:
            name = prettify_class_name(model.__name__)

        super(ModelView, self).__init__(name, endpoint, url, static_folder)

        # Scaffolding
        self._scaffold()

    def _scaffold(self):
        "Calculate various instance variables"
        # List view
        self._list_columns = self.get_list_columns()
        self._link_column = self.get_link_column()
        self._sortable_columns = self.get_sortable_columns()

        # Detail view
        if self.can_view_details:
            self._details_columns = self.get_details_columns()

        # Export view
        self._export_columns = self.get_export_columns()

        # Labels
        if self.column_labels is None:
            self.column_labels = {}

        # Forms
        self._form_fields = self.get_form_fields()

        # Search

        # Choices
        if self.column_choices:
            self._column_choices = dict([
                (column, dict(choices))
                for column, choices in self.column_choices.items()
            ])
        else:
            self.column_choices = self._column_choices_map = dict()

        # Column formatters
        if self.column_formatters_export is None:
            self.column_formatters_export = self.column_formatters

        # Type formatters
        if self.column_type_formatters is None:
            self.column_type_formatters = dict(typefmt.BASE_FORMATTERS)

        if self.column_type_formatters_export is None:
            self.column_type_formatters_export = dict(
                typefmt.EXPORT_FORMATTERS
            )

        if self.column_descriptions is None:
            self.column_descriptions = dict()

        # Filters

        # Form rendering rules

        # Process form rules

    # Endpoint
    def _get_endpoint(self, endpoint):
        if endpoint:
            return super(ModelView, self)._get_endpoint(endpoint)
        return self.model.__name__.lower()

    # Forms
    def create_form(self):
        if self.form:
            return self.form

        field_args = {field: {'label': label}
                      for field, label in self._form_fields}

        if self.field_args:
            field_args.update(self.field_args)

        # TODO: Caching form creation
        return build_form(
            self.model,
            base_class=self.form_base_class,
            only=self.form_columns,
            exclude=self.form_excluded_columns,
            field_args=field_args,
            ignore_hidden=self.ignore_hidden,
            extra_fields=self.form_extra_fields)

    def get_column_name(self, field):
        """
        Return a human-readable column name.
        """
        if self.column_labels and field in self.column_labels:
            return self.column_labels[field]
        return tools.column_name(field)

    def get_column_names(self, only_columns=None, excluded_columns=None):
        """
        Returns a list of tuples with the model field name and formatted field
        name.
        """
        if not only_columns:
            only_columns = self.build_column_list()
        if excluded_columns:
            only_columns = [c for c in only_columns
                            if c not in excluded_columns]
        return [(c, self.get_column_name(c)) for c in only_columns]

    def get_list_columns(self):
        """
        Uses `get_column_names` to get a list of tuple with the model field
        name and formatted name.
        """
        return self.get_column_names(
            only_columns=self.column_list,
            excluded_columns=self.column_exclude_list,
        )

    def build_column_list(self):
        return tools.list_columns(self.model,
                                  self.column_display_all_relations,
                                  self.column_display_pk)

    def get_link_column(self):
        if self.column_details_link in self._list_columns:
            return self.column_details_link
        elif isinstance(self.column_details_link, int):
            return self._list_columns[self.column_details_link][0]
        else:
            return None

    def get_form_fields(self):
        return self.get_column_names(
            only_columns=self.form_columns or tools.list_columns(self.model),
            excluded_columns=self.form_excluded_columns,
        )

    def get_details_columns(self):
        return self.get_column_names(
            only_columns=self.column_details_list,
            excluded_columns=self.column_details_exclude_list,
        )

    def get_export_columns(self):
        return self.get_column_names(
            only_columns=self.column_export_list or self.column_list,
            excluded_columns=self.column_export_exclude_list,
        )

    def get_sortable_columns(self):
        self._sortable_joins = dict()

        if self.column_sortable_list is None:
            return self.build_sortable_columns()
        else:
            result = dict()

            for c in self.column_sortable_list:
                if isinstance(c, tuple):
                    column, path = tools.get_field_with_path(self.model, c[1])
                    column_name = c[0]
                else:
                    column, path = tools.get_field_with_path(self.model, c)
                    column_name = text_type(c)

                if path and hasattr(path[0], 'property'):
                    self._sortable_joins[column_name] = path
                elif path:
                    raise Exception("For sorting columns in a related table, "
                                    "column_sortable_list requires a string "
                                    "like '<relation name>.<column name>'. "
                                    "Failed on: {0}".format(c))
                else:
                    # column is in same table, use only model attribute name
                    if getattr(column, 'key', None) is not None:
                        column_name = column.key
                    else:
                        column_name = c

                # column_name must match column_name used in `get_list_columns`
                result[column_name] = column

            return result

    def build_sortable_columns(self):
        """
        Return a dictionary of sortable columns.
        """
        return tools.sortable_columns(self.model, self.column_display_pk)

    def get_save_return_url(self, model, is_created=False):
        "Return url where use is redirected after successful form save."
        return get_redirect_target() or self.get_url('.index_view')

    # Helpers
    def is_sortable(self, name):
        """
        Verify if column is sortable.
        """
        return name.lower() in (x.lower() for x in self._sortable_columns)

    def _get_column_by_idx(self, idx):
        "Return column index by"
        if idx is None or idx < 0 or idx >= len(self._list_columns):
            return None
        return self._list_columns[idx]

    # DB related API
    def get_query(self):
        "Return a query for the model type."
        return self.session.query(self.model)

    def get_count_query(self):
        "Return a the count query for the model type"
        return self.session.query(func.count('*')).select_from(self.model)

    def _order_by(self, query, joins, sort_joins, sort_field, sort_desc):
        if sort_field is not None:
            # Handle joins
            query, joins, alias = self._apply_path_joins(query, joins, sort_joins, inner_join=False)
            column = sort_field if alias is None else getattr(alias, sort_field.key)

            if sort_desc:
                if isinstance(column, tuple):
                    query = query.order_by(*map(desc, column))
                else:
                    query = query.order_by(desc(column))
            else:
                if isinstance(column, tuple):
                    query = query.order_by(*column)
                else:
                    query = query.order_by(column)

        return query, joins

    def _get_default_order(self):
        "Return default sort order"
        order = None
        if self.column_default_sort:
            if isinstance(self.column_default_sort, tuple):
                order = self.column_default_sort
            else:
                order = self.column_default_sort, False

        if order is not None:
            field, direction = order
            attr, joins = tools.get_field_with_path(self.model, field)
            return attr, joins, direction

        return None

    def _apply_sorting(self, query, joins, sort_column, sort_desc):
        if sort_column is not None:
            if sort_column in self._sortable_columns:
                sort_field = self._sortable_columns[sort_column]
                sort_joins = self._sortable_joins.get(sort_column)

                query, joins = self._order_by(query, joins, sort_joins,
                                              sort_field, sort_desc)
        else:
            order = self._get_default_order()

            if order:
                sort_field, sort_joins, sort_desc = order
                query, joins = self._order_by(query, joins, sort_joins,
                                              sort_field, sort_desc)
        return query, joins

    def _apply_path_joins(self, query, joins, path, inner_join=True):
        last = None
        if path:
            for item in path:
                key = (inner_join, item)
                alias = joins.get(key)

                if key not in joins:
                    if not isinstance(item, Table):
                        alias = aliased(item.property.mapper.class_)

                    fn = query.join if inner_join else query.outerjoin

                    if last is None:
                        query = fn(item) if alias is None else fn(alias, item)
                    else:
                        prop = getattr(last, item.key)
                        query = fn(prop) if alias is None else fn(alias, prop)

                    joins[key] = alias

                last = alias

        return query, joins, last

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 page_size=None):
        """
        Return a paginated list and sorted list of model from the data source.
        """

        # Will contain join paths with optional aliased object
        joins = {}
        count_joins = {}

        query = self.get_query()
        count_query = self.get_count_query() if not self.simple_pager else None

        # Apply search criteria

        # Apply filters

        # Calculate number of rows if necessary
        count = count_query.scalar() if count_query else None

        # Apply auto join

        # Apply sorting
        query, joins = self._apply_sorting(query, joins, sort_column, sort_desc)

        # Apply pagination

        # Excecute
        query = query.all()

        return count, query

    def get_one(self, id):
        "Return one model by its id."
        return self.session.query(self.model).get(id)

    def handle_view_exception(self, exc):
        if isinstance(exc, IntegrityError):
            flash(gettext('Integrity error. %(message)s', message=exc),
                  'error')
            return True

        if isinstance(exc, ValidationError):
            flash(exc, 'error')
            return True

        if self.plumbum.app.config.get('PLUMBUM_RAISE_ON_VIEW_EXCEPTION'):
            raise

        if self.plumbum.app.debug:
            raise

        return False

    def create_model(self, form):
        "Create model from the form."
        try:
            model = self.model()
            form.populate_obj(model)
            self.session.add(model)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s', error=ex),
                      'error')

            self.session.rollback()
            return False

        return model

    def update_model(self, form, model):
        "Update model from the form."
        raise NotImplementedError()

    def delete_model(self, model):
        "Delete model"
        raise NotImplementedError()

    # Various helpers
    @property
    def empty_list_message(self):
        return gettext('There are no items in the table.')

    # URL generation helpers
    def _get_list_extra_args(self):
        "Return arguments from query string"
        args = request.args
        return ViewArgs(page=args.get('page', 0, type=int),
                        page_size=args.get('page_size', 0, type=int),
                        sort=args.get('sort', None, type=int),
                        sort_desc=args.get('desc', None, type=int),
                        search=args.get('search', None),
                        filters=None)

    def _get_filters(self, filters):
        "Get active filters as dictionary of URL arguments and values"
        kwargs = {}

        if filters:
            for i, pair in enumerate(filters):
                idx, flt_name, value = pair

                key = 'flt{}_{}'.format(i, self.get_filter_arg(idx,
                                        self._filters[idx]))
                kwargs[key] = value
        return kwargs

    def _get_list_url(self, view_args):
        "Generate page URL with current page, sort columns, etc."
        page = view_args.page or None
        desc = 1 if view_args.sort_desc else None

        kwargs = dict(page=page, sort=view_args.sort, desc=desc,
                      search=view_args.search)
        kwargs.update(view_args.extra_args)

        if view_args.page_size:
            kwargs['page_size'] = view_args.page_size

        kwargs.update(self._get_filters(view_args.filters))

        return self.get_url('.index_view', **kwargs)

    def _get_list_value(self, context, model, name, column_formatters,
                        column_type_formatters):
        "Returns the value to be displayed"
        column_fmt = column_formatters.get(name)
        if column_fmt is not None:
            value = column_fmt(self, context, model, name)
        else:
            value = tools.get_field_value(model, name)

        choices_map = self._column_choices_map.get(name, {})
        if choices_map:
            return choices_map.get(value) or value

        type_fmt = None
        for typeobj, formatter in column_type_formatters.items():
            if isinstance(value, typeobj):
                type_fmt = formatter
                break
        if type_fmt is not None:
            value = type_fmt(self, value)

        return value

    @contextfunction
    def get_list_value(self, context, model, name):
        "Returns the value to be displayed in the list view"
        return self._get_list_value(
            context,
            model,
            name,
            self.column_formatters,
            self.column_type_formatters,
        )

    def get_export_value(self, model, name):
        """
        Returns the value to be displayed in export.
        """
        return self._get_list_value(
            None,
            model,
            name,
            self.column_formatters_export,
            self.column_type_formatters_export,
        )

    # Views
    @expose('/')
    def index_view(self):
        "List view"
        # Grab parameters form URL
        view_args = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get page size
        page_size = view_args.page_size or self.page_size

        # Get count and data
        count, data = self.get_list(view_args.page, sort_column,
                                    view_args.sort_desc, view_args.search,
                                    view_args.filters, page_size=page_size)

        # Calculate number of pages
        if count is not None and page_size:
            num_pages = int(ceil(count / float(page_size)))
        elif not page_size:
            num_pages = 0  # hide pager for unlimited page_size
        else:
            num_pages = None  # use simple pager

        def sort_url(column, invert=False, desc=None):
            if not desc and invert and not view_args.sort_desc:
                desc = 1

            return self._get_list_url(view_args.clone(sort=column, sort_desc=desc))

        return self.render(
            self.list_template,
            data=data,

            # List
            list_columns=self._list_columns,
            link_column=self._link_column,

            # Pagination
            count=count,
            num_pages=num_pages,
            page=view_args.page,
            page_size=page_size,

            # Sorting
            sort_column=view_args.sort,
            sort_desc=view_args.sort_desc,
            sort_url=sort_url,

            # Misc
            get_value=self.get_list_value,
            return_url=self._get_list_url(view_args),
        )

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        "Create model view"
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_create:
            return redirect(return_url)

        form_class = self.create_form()
        form = form_class()

        if form.validate_on_submit():
            model = self.create_model(form)
            print('model:', model)
            if model:
                flash(gettext('Record was successfully created.'), 'success')
                if '_add_another' in request.form:
                    return redirect(request.url)
                elif '_continue_editing' in request.form:
                    # if we have a valid model, try to go to the edit view
                    if model is not True:
                        url = self.get_url('.edit_view',
                                           id=self.get_pk_value(model),
                                           url=return_url)
                    else:
                        url = return_url
                    return redirect(url)
                else:
                    # save button
                    return redirect(self.get_save_return_url(model,
                                                             is_created=True))

        if self.create_modal and request.args.get('modal'):
            template = self.create_modal_template
        else:
            template = self.create_template

        return self.render(template,
                           form=form,
                           return_url=return_url)

    @expose('/<int:pk>')
    def details_view(self, pk=None):
        """Details model view"""
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_view_details:
            return redirect(return_url)

        if pk is None:
            return redirect(return_url)

        model = self.get_one(pk)

        if model is None:
            flash(gettext('Record does not exist.'), 'error')
            return redirect(return_url)

        template = self.details_template

        return self.render(template,
                           model=model,
                           details_columns=self._details_columns,
                           get_value=self.get_list_value,
                           return_url=return_url)

    # Exports
    @expose('/export/<export_type>/')
    def export(self, export_type):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_export or (export_type not in self.export_types):
            flash(gettext('Permission denied.'), 'error')
            return redirect(return_url)

        if export_type == 'csv':
            return self._export_csv(return_url)
        else:
            return self._export_tablib(export_type, return_url)

    def _export_csv(self, return_url):
        "Export a CSV of records as a stream."
        count, data = self._export_data()

        class Echo(object):
            def write(self, value):
                return value

        writer = csv.writer(Echo())

        def generate():
            titles = [c[1] for c in self._export_columns]
            yield writer.writerow(titles)

            for row in data:
                vals = [self.get_export_value(row, c[0])
                        for c in self._export_columns]
                yield writer.writerow(vals)

        filename = self.get_export_filename(export_type='csv')
        disposition = 'attachment;filename={}'.format(
            secure_filename(filename)
        )

        return Response(
            stream_with_context(generate()),
            headers={'Content-Disposition': disposition},
            mimetype='text/csv'
        )

    def _export_tablib(self, export_type, return_url):
        """
        Exports a variety of formates using the tablib library.
        """
        if tablib is None:
            flash(gettext('Tablib dependency not installed'), 'error')
            return redirect(return_url)

        filename = self.get_export_filename(export_type)
        disposition = 'attachment;filename={}'.format(
            secure_filename(filename)
        )
        mimetype, encoding = mimetypes.guess_type(filename)

        if not mimetype:
            mimetype = 'application/octet-stream'
        if encoding:
            mimetype = '{}; charset={}'.format(mimetype, encoding)

        ds = tablib.Dataset(headers=[str(c[1]) for c in self._export_columns])

        count, data = self._export_data()

        for row in data:
            vals = [self.get_export_value(row, c[0])
                    for c in self._export_columns]
            ds.append(vals)

        try:
            try:
                response_data = ds.export(format=export_type)
            except AttributeError:
                response_data = getattr(ds, export_type)
        except (AttributeError, tablib.UnsupportedFormat):
            flash(lazy_gettext('Export type "%(type)s" is not supported.',
                               type=export_type), 'error')
            return redirect(return_url)

        return Response(
            response_data,
            headers={'Content-Disposition': disposition},
            mimetype=mimetype,
        )

    def _export_data(self):
        for col, f in self.column_formatters_export.items():
            # skip checkin columns not being exported
            if col not in [col for col, _ in self._export_columns]:
                continue

            if f.__name__ == 'inner':
                raise NotImplementedError(
                    "Macros are not implemented in export. Exclude column in "
                    "column_formatters_export, column_export_list, or "
                    "column_export_exclude_list. Column: {}".format(col)
                )

        # Grab parameters from URL
        view_args = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get count and data
        count, data = self.get_list(0, sort_column, view_args.sort_desc,
                                    view_args.search, view_args.filters,
                                    page_size=self.export_max_rows)

        return count, data

    def get_export_filename(self, export_type='csv'):
        return "{}_{}.{}".format(
            self.name,
            time.strftime("%Y-%m-%d_%H-%M-%S"),
            export_type
        )
