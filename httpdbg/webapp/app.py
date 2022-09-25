# -*- coding: utf-8 -*-
import logging
import os

from flask import Flask
from flask_restful import Api

from httpdbg.webapp.api import (
    Request,
    RequestContentDown,
    RequestContentUp,
    RequestList,
)

app = Flask("httpdbgwebapp")
app.static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static")

api = Api(app)

# remove flask message
logging.getLogger("werkzeug").disabled = True
os.environ["WERKZEUG_RUN_MAIN"] = "true"


@app.route("/")
def root():
    return app.send_static_file("index.htm")


@app.route("/config")
def config():
    return app.send_static_file("config.htm")


@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    response.cache_control.no_cache = True
    response.cache_control.no_store = True
    response.cache_control.private = True
    response.cache_control.public = False
    return response


api.add_resource(RequestList, "/requests")
api.add_resource(Request, "/request/<req_id>")
api.add_resource(RequestContentDown, "/request/<req_id>/down")
api.add_resource(RequestContentUp, "/request/<req_id>/up")
