# -*- coding: utf-8 -*-

import os.path
from functools import wraps

from flask import Blueprint, render_template, abort, g, url_for
from jinja2 import contextfunction
from flask_webpack import Webpack

from .menu import MenuView
from .babel import gettext, ngettext, lazy_gettext
from . import tools


CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))


def expose(url='/', methods=('GET',)):
    """
    Decorator to expose views in your view classes.
    """
    def wrap(f):
        if not hasattr(f, '_urls'):
            f._urls = []
        f._urls.append((url, methods))
        return f
    return wrap


def _wrap_view(f):
    if hasattr(f, '_wrapped'):
        return f

    @wraps(f)
    def inner(self, *args, **kwargs):
        tools.set_current_view(self)

        abort = self._handle_view(f.__name__, **kwargs)
        if abort is not None:
            return abort
        return self._run_view(f, *args, **kwargs)

    inner._wrapped = True
    return inner


class PlumbumViewMeta(type):
    """
    View metaclass.
    """
    def __init__(cls, classname, bases, fields):
        type.__init__(cls, classname, bases, fields)

        cls._urls = []
        cls._default_view = None

        for p in dir(cls):
            attr = getattr(cls, p)

            if hasattr(attr, '_urls'):
                for url, methods in attr._urls:
                    cls._urls.append((url, p, methods))

                    if url == '/':
                        cls._default_view = p

                # Wrap views
                setattr(cls, p, _wrap_view(attr))


class BaseView(metaclass=PlumbumViewMeta):
    """
    Base administrative view.
    """

    name = None

    @property
    def _template_args(self):
        args = getattr(g, '_plumbum_template_args', None)
        if args is None:
            args = g._plumbum_template_args = dict()
        return args

    def __init__(self, name=None, endpoint=None, url=None, static_folder=None,
                 static_url_path=None, menu_class_name=None,
                 menu_icon_type=None, menu_icon_value=None):
        self.name = name if name else self.name
        self.endpoint = self._get_endpoint(endpoint)
        self.url = url
        self.static_folder = static_folder
        self.static_url_path = static_url_path
        self.menu = None
        self._sub_menu = []

        self.menu_class_name = menu_class_name
        self.menu_icon_type = menu_icon_type
        self.menu_icon_value = menu_icon_value

        self.plumbum = None
        self.blueprint = None

        self._sub_views = []

        if self._default_view is None:
            raise Exception(
                "no default view for {}".format(self.__class__.__name__)
            )

    def _get_endpoint(self, endpoint):
        if endpoint:
            return endpoint
        return self.__class__.__name__.lower()

    def _get_view_url(self, plumbum, url):
        if url is None:
            if plumbum.url != '/':
                url = '{}/{}'.format(plumbum.url, self.endpoint)
            else:
                if self == plumbum.index_view:
                    url = '/'
                else:
                    url = '/{}'.format(self.endpoint)
        else:
            if not url.startswith('/'):
                url = '{}/{}'.format(plumbum.url, url)

        return url

    def create_blueprint(self, plumbum):
        """
        Create Flask blueprint
        """
        self.plumbum = plumbum

        if not self.static_url_path:
            self.static_url_path = plumbum.static_url_path

        self.url = self._get_view_url(plumbum, self.url)

        if self.url == '/':
            self.url = None

            if not self.static_url_path:
                self.static_folder = 'static'
                self.static_url_path = '/static/plumbum'

        if self.name is None:
            self.name = tools.prettify_class_name(self.__class__.__name__)

        self.blueprint = Blueprint(self.endpoint, __name__,
                                   url_prefix=self.url,
                                   subdomain=self.plumbum.subdomain,
                                   template_folder='templates',
                                   static_folder=self.static_folder,
                                   static_url_path=self.static_url_path)

        for url, name, methods in self._urls:
            self.blueprint.add_url_rule(url, name, getattr(self, name),
                                        methods=methods)

        for view in self._sub_views:
            for url, name, methods in view._urls:
                self.blueprint.add_url_rule(url, self.endpoint + '_' + name, getattr(view, name),
                                            methods=methods)

        return self.blueprint

    def render(self, template, **kwargs):
        """
        Render template
        """

        # Only for debug purposes
        @contextfunction
        def get_context(context):
            return context

        from pprint import pformat

        kwargs['context'] = get_context
        kwargs['callable'] = callable
        kwargs['pformat'] = pformat
        # End debug purpose, delete pelase

        # Sotre self as view
        kwargs['view'] = self
        kwargs['plumbum_base_template'] = self.plumbum.base_template

        # Provide i18n support even if flask-babelex is not installed.
        kwargs['_gettext'] = gettext
        kwargs['_ngettext'] = ngettext

        # Expose get_url helper
        kwargs['get_url'] = self.get_url

        # Contribute extra arguments
        kwargs.update(self._template_args)

        return render_template(template, **kwargs)

    def is_visible(self):
        return True

    def is_accessible(self):
        return True

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return self.inaccessible_callback(name, **kwargs)

    def _run_view(self, fn, *args, **kwargs):
        return fn(self, *args, **kwargs)

    def inaccessible_callback(self, name, **kwargs):
        return abort(403)

    def get_url(self, endpoint, **kwargs):
        return url_for(endpoint, **kwargs)

    # Handle sub-views
    def add_subview(self, view):
        self._sub_views.append(view)
        self._sub_menu.append(MenuView(view.name, view))

    @property
    def sub_menu(self):
        return self._sub_menu


class PlumbumIndexView(BaseView):

    def __init__(self, name=None, endpoint=None, url=None,
                 template='plumbum/index.html', menu_class_name=None,
                 menu_icon_type=None, menu_icon_value=None):
        super(PlumbumIndexView, self).__init__(name or lazy_gettext('Home'),
                                               endpoint or 'plumbum',
                                               '/plumbum' if url is None else
                                               url, 'static',
                                               menu_class_name=menu_class_name,
                                               menu_icon_type=menu_icon_type,
                                               menu_icon_value=menu_icon_value)
        self._template = template

    @expose()
    def index(self):
        return self.render(self._template)


class Plumbum(object):
    """
    Collection of the plumbum views.
    """
    def __init__(self, app=None, name=None, url=None, subdomain=None,
                 index_view=None, translations_path=None, endpoint=None,
                 static_url_path=None, base_template=None):
        self.app = None
        self.translations_path = translations_path
        self._views = []
        self._menu = []
        self._menu_links = []

        if name is None:
            name = 'Plumbum'
        self.name = name
        self.app_name = 'Plumbum'

        self.static_url_path = static_url_path
        self.subdomain = subdomain
        self.base_template = base_template or 'plumbum/base.html'

        # Add index view
        self._set_index_view(index_view=index_view, endpoint=endpoint, url=url)

        # Register with application
        if app is not None:
            self._init_app()

    def _set_index_view(self, index_view=None, endpoint=None, url=None):
        self.index_view = index_view or PlumbumIndexView(endpoint=endpoint,
                                                         url=url)
        self.endpoint = self.index_view.endpoint
        self.url = self.index_view.url

        self.add_view(self.index_view)

    def add_view(self, view):

        # accepts non instantiated class, then instantiate without arguments
        if isinstance(view, type):
            view = view()

        self._views.append(view)

        if self.app is not None:
            self.app.register_blueprint(view.create_blueprint(self))

        self.add_menu_item(MenuView(view.name, view))

    def add_menu_item(self, menu_item, target_category=None):
        "Add menu item to menu tree hierarchy"
        self._menu.append(menu_item)

    def init_app(self, app, index_view=None, endpoint=None, url=None):
        self.app = app
        self.app.config.setdefault('PLUMBUM_DEBUG_TEMPLATE', False)

        self._init_app()

        # Register index view
        if index_view is not None:
            self._set_index_view(index_view=index_view, endpoint=endpoint,
                                 url=url)

        # Register views
        for view in self._views:
            app.register_blueprint(view.create_blueprint(self))

    def _init_app(self):
        if not hasattr(self.app, 'extensions'):
            self.app.extensions = dict()

        plumbums = self.app.extensions.get('plumbum', [])

        for p in plumbums:
            if p.endpoint == self.endpoint:
                raise Exception('Cannot have two Plumbum() instance with same '
                                'endpoint name.')
            if p.url == self.url and p.subdomain == self.subdomain:
                raise Exception('Cannot assign two Plumbum() instances with '
                                'same URL and subdomain to the same '
                                'application.')

        plumbums.append(self)
        self.app.extensions['plumbum'] = plumbums

        # Initialize Webpack plugin
        # FIXME: Hardcoded, move to appropiate place
        self.app.config.update({
            'WEBPACK_MANIFEST_PATH': '{}/static/webpack/manifest.json'.format(
                CURRENT_PATH
            ),
        })
        webpack = Webpack()
        webpack.init_app(self.app)

        if self.app.debug:
            self._attach_show_urls_view()

    def _attach_show_urls_view(self):
        @self.app.route('/urls')
        def show_urls():
            column_headers = ('Rule', 'Endpoint', 'Methods')
            order = 'rule'
            rows = [('-'*4, '-'*8, '-'*9)]  # minimal values to take
            rules = sorted(self.app.url_map.iter_rules(),
                           key=lambda rule: getattr(rule, order))
            for rule in rules:
                rows.append(
                    (rule.rule, rule.endpoint, ', '.join(rule.methods))
                )

            rule_l = len(max(rows, key=lambda r: len(r[0]))[0])
            ep_l = len(max(rows, key=lambda r: len(r[1]))[1])
            meth_l = len(max(rows, key=lambda r: len(r[2]))[2])

            str_template = '%-' + str(rule_l) + 's' + \
                           ' %-' + str(ep_l) + 's' + \
                           ' %-' + str(meth_l) + 's'
            table_width = rule_l + 2 + ep_l + 2 + meth_l

            out = (str_template % column_headers) + '\n' + '-' * table_width
            for row in rows[1:]:
                out += '\n' + str_template % row

            return out + '\n'

    def menu(self):
        "Return the menu hierarchy"
        return self._menu

    def menu_links(self):
        "Return menu links"
        return self._menu_links
