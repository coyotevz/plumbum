# -*- coding: utf-8 -*-

from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_babelex import Babel, Domain, lazy_gettext

from wtforms import validators

from plumbum import Plumbum, ModelView

sqla_domain = Domain(domain='sqla-babel', dirname='locales')

# Create application
app = Flask(__name__)
babel = Babel(app, default_domain=sqla_domain)

app.config['SECRET_KEY'] = '1234'

app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sample_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PLUMBUM_DEBUG_TEMPLATE'] = True

db = SQLAlchemy(app)


@babel.localeselector
def get_locale():
    override = request.args.get('lang')

    if override:
        session['lang'] = override

    return session.get('lang', 'en')


# Create models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __str__(self):
        return self.username


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User, backref='posts')

    def __str__(self):
        return self.title


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))

    def __str__(self):
        return self.name


class UserView(ModelView):
    can_export = True
    export_types = ['csv', 'tsv', 'xls', 'xlsx', 'json', 'yaml']
    column_labels = {
        'first_name': lazy_gettext('First Name'),
        'last_name': lazy_gettext('Last Name'),
        'username': lazy_gettext('Username'),
        'email': lazy_gettext('Email'),
        'posts': lazy_gettext('Posts'),
    }


# Customize Post model view
class PostView(ModelView):
    # Visible columns in the list view
    column_exclude_list = ['text']
    column_labels = {
        'title': lazy_gettext('Post Title'),
        'date': lazy_gettext('Date'),
        'user': lazy_gettext('User'),
        'tags': lazy_gettext('Tags'),
    }

    field_args = {
        'text': {
            'label': lazy_gettext('Big Text'),
            'validators': [validators.Required()],
        }
    }

    def __init__(self, session):
        # Just call parent class with predefined model.
        super(PostView, self).__init__(Post, session, lazy_gettext('Post'))


pb = Plumbum(app, name=lazy_gettext('Example: SQLAlchemy + Babel'), url='/')

pb.add_view(UserView(User, db.session, lazy_gettext('User')))
pb.add_view(ModelView(Tag, db.session, lazy_gettext('Tag')))
pb.add_view(PostView(db.session))


if __name__ == "__main__":
    db.create_all()
    app.run(port=8000)
