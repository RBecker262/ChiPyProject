from flask import Flask


webapp = Flask(__name__)
webapp.config.from_object('config')

from webapp import views
