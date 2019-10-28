from flask import Flask, cli, render_template
from flasgger import Swagger
from recon.core import base
from recon.core.constants import BANNER_WEB
from recon.core.web.db import Tasks
from redis import Redis
import os
import rq

# disable the development server warning banner
cli.show_server_banner = lambda *x: None

print(BANNER_WEB)

# create an application-wide framework and tasks instance
recon = base.Recon(check=False, analytics=False, marketplace=False)
recon.start(base.Mode.WEB)
tasks = Tasks(recon)

# configuration
DEBUG = False
SECRET_KEY = 'we keep no secrets here.'
JSON_SORT_KEYS = False
REDIS_URL = os.environ.get('REDIS_URL', 'redis://')
SWAGGER = {
    'title': 'Swagger',
    'info': {
        'title': 'Recon-API',
        'description': 'A RESTful API for Recon-ng',
        'version': '0.0.1',
    },
    'uiversion': 3,
    'specs_route': '/api/',
}
WORKSPACE = recon.workspace.split('/')[-1]
print((f" * Workspace initialized: {WORKSPACE}"))

def create_app():

    # setting the static_url_path to blank serves static files from the web root
    app = Flask(__name__, static_url_path='')
    app.config.from_object(__name__)

    Swagger(app, template_file='definitions.yaml')

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('recon-tasks', connection=app.redis)

    @app.after_request
    def disable_cache(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    @app.route('/')
    def index():
        return render_template('index.html', workspaces=recon._get_workspaces())

    from recon.core.web.api import resources
    app.register_blueprint(resources)

    return app
