# -*- coding: utf-8 -*-

from flask import Flask
from plumbum import Plumbum, BaseView, expose


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')


app = Flask(__name__)
app.debug = True

pb = Plumbum(app, name="Example: Quickstart2")
pb.add_view(MyView(name='Hello'))

if __name__ == "__main__":
    app.run(debug=True)
