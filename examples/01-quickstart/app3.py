# -*- coding: utf-8 -*-

from flask import Flask
from plumbum import Plumbum, BaseView, expose


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')


app = Flask(__name__)
app.debug = True

pb = Plumbum(app, name="Example: Quickstart3")
pb.add_view(MyView(name='Hello 1', endpoint='test1'))
pb.add_view(MyView(name='Hello 2', endpoint='test2'))
pb.add_view(MyView(name='Hello 3', endpoint='test3'))

if __name__ == "__main__":
    app.run(debug=True)
