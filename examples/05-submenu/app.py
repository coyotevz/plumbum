# -*- coding: utf-8 -*-

from flask import Flask
import plumbum


# Create custom view
class MyPlumbumView(plumbum.BaseView):
    @plumbum.expose('/')
    def index(self):
        return self.render('myplumbum.html')


class AnotherPlumbumView(plumbum.BaseView):
    @plumbum.expose('/')
    def index(self):
        return self.render('anotherplumbum.html')

    @plumbum.expose('/test/')
    def test(self):
        return self.render('test.html')


class MyFirstSubView(plumbum.BaseView):
    @plumbum.expose('/')
    def index(self):
        return self.render('myfirstsubview.html')


another_plumbum_view = AnotherPlumbumView(name="view2")
another_plumbum_view.add_subview(MyFirstSubView(name="sub-view1"))


# Create flask app
app = Flask(__name__, template_folder='templates')
app.debug = True


# Flask views
@app.route('/')
def index():
    return '<a href="/pb/">Click me to get to Plumbum!</a>'


# Create plumbum interface
pb = plumbum.Plumbum(name="Example: Simple Views", url='/pb')
pb.add_view(MyPlumbumView(name="view1"))
pb.add_view(another_plumbum_view)
pb.init_app(app)

if __name__ == "__main__":
    app.run()
