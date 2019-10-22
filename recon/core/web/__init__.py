from flask import Flask, request, abort
from recon.core import base
import os

# print welcome message
welcome = '''\
*************************************************************************
 * Welcome to Recon-web, the analytics and reporting engine for Recon-ng!
 * This is a web-based user interface. Open the URL below in your browser to begin.
*************************************************************************\
'''
print(welcome)

recon = base.Recon(analytics=False)
recon.start(base.Mode.CLI)

# configuration
DEBUG = False
SECRET_KEY = 'we keep no secrets here.'
JSON_SORT_KEYS = False
WORKSPACE = recon.workspace.split('/')[-1]
print((f" * Workspace initialized: {WORKSPACE}"))

def create_app():

    # setting the static_url_path to blank serves static files from the web root
    app = Flask(__name__, static_url_path='')
    app.config.from_object(__name__)

    @app.after_request
    def disable_cache(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    from recon.core.web.views import core
    app.register_blueprint(core)
    from recon.core.web.views import resources
    app.register_blueprint(resources)

    return app
