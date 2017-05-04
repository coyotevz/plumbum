# -*- coding: utf-8 -*-

from flask import Flask
from plumbum import Plumbum


app = Flask(__name__)
app.debug = True

pb = Plumbum(app, name="Example: Quickstart")

if __name__ == "__main__":
    app.run(debug=True)
