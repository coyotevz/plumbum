# -*- coding: utf-8 -*-

from urllib.parse import urljoin, urlparse

from sqlalchemy import func

from flask import request
from jinja2 import contextfunction
from ..base import BaseView, expose, prettify_class_name
from ..form import BaseForm, build_form
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
    can_view_details = False
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
            column_exclude_list = ('last_name', 'emial')
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

    column_type_formatters = None
    """
    Dictionary of value type formatters to be used in the list view.
    """

    # Form settings
    form = None
    """
    Form class. Override if yo want to use custom form for your model
    """

    form_base_class = BaseForm
    """
    Base form class. Will be used by form scaffolding function when creating model form.
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

    # Pagination settings
    page_size = 20
    """
    Default page size for pagination.
    """

    can_set_page_size = False
    """
    Allow to select page size via dropdown list
    """

    simple_list_pager = False
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
        self._list_columns = tools.column_names(
            model=self.model,
            only_columns=self.column_list,
            excluded_columns=self.column_exclude_list,
            display_all_relations=self.column_display_all_relations,
            display_pk=self.column_display_pk,
        )

        # Detail view

        # Export view

        # Labels

        # Forms

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

        # Type formatters
        if self.column_type_formatters is None:
            self.column_type_formatters = dict(typefmt.BASE_FORMATTERS)

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

        # TODO: Caching form creation
        return build_form(
            self.model,
            base_class=self.form_base_class,
            only=self.form_columns,
            exclude=self.form_excluded_columns,
            field_args=self.field_args,
            ignore_hidden=self.ignore_hidden,
            extra_fields=self.form_extra_fields)

    # Helpers
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

    def get_list(self, page, sort_field, sort_desc, search, filters,
                 page_size=None):
        "Return a paginated list and sorted list of model from the data source."
        joins = {}
        count_joins = {}

        query = self.get_query()
        count_query = self.get_count_query() if not self.simple_list_pager else None

        # Apply search criteria

        # Apply filters

        # Calculate number of rows if necessary
        count = count_query.scalar() if count_query else None

        # Apply auto join

        # Apply sorting

        # Apply pagination

        # Excecute
        query = query.all()

        return count, query

    def get_one(self, id):
        "Return one model by its id."
        return self.session.query(self.model).get(id)

    def create_model(self, form):
        "Create model from the form."
        raise NotImplementedError()

    def update_model(self, form, model):
        "Update model from the form."
        raise NotImplementedError()

    def delete_model(self, model):
        "Delete model"
        raise NotImplementedError()

    # Various helpers
    def get_empty_list_message(self):
        return 'There are no items in the table.'


    # URL generation helpers
    def _get_list_extra_args(self):
        "Return arguments from query string"
        args = request.args
        return ViewArgs(page=args.get('page', 0, type=int),
                        page_size=args.get('page_size', 0,type=int),
                        sort=args.get('sort', None, type=int),
                        sort_desc=args.get('desc', None, type=int),
                        search=args.get('search', None),
                        filters=None)

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

        return self.render(
            self.list_template,
            data=data,

            # List
            list_columns=self._list_columns,

            # Pagination
            count=count,
            page=view_args.page,
            page_size=page_size,

            # Misc
            get_value=self.get_list_value,
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
            # TODO: handle valid form and redirect
            pass

        if self.create_modal and request.args.get('modal'):
            template = self.create_modal_template
        else:
            template = self.create_template

        return self.render(template,
                           form=form,
                           return_url=return_url)
