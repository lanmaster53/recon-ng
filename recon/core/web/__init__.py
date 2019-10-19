from flask import Flask, g, request, abort
from recon.core.web.utils import connect_db, get_workspaces
import logging
import os

#logging.basicConfig(level=logging.INFO)

# print welcome message
welcome = '''\
*************************************************************************
 * Welcome to Recon-web, the analytics and reporting engine for Recon-ng!
 * This is a web-based user interface. Open the following URL in your browser to begin.'''
print(welcome)

# configuration
DEBUG = False
SECRET_KEY = 'we keep no secrets here.'
HOME_DIR = os.path.join(os.path.expanduser('~'), '.recon-ng')
DATABASE = os.path.join(HOME_DIR, 'workspaces', '{}', 'data.db')
KEYS_DB = os.path.join(HOME_DIR, 'keys.db')
JSON_SORT_KEYS = False

def create_app():

    # setting the static_url_path to blank serves static files from the web root
    app = Flask(__name__)#, static_url_path='')
    app.config.from_object(__name__)

    @app.before_request
    def open_db():
        '''Opens a new database connection if there is none yet for the
        current application context.'''
        if not hasattr(g, 'db'):
            # parse the workspace name from the url if present
            workspace = None
            if request.view_args:
                workspace = request.view_args.get('workspace')
            if workspace:
                # validate the provided workspace
                if workspace not in get_workspaces():
                    abort(404)
                # resolve the workspace's database path
                database = app.config['DATABASE'].format(workspace)
                # create and store the database connection
                g.db = connect_db(database)
                g.workspace = workspace
                app.logger.info(f"Database connection created for {workspace} workspace.")

    @app.teardown_appcontext
    def close_db(error):
        '''Closes the database connection at the end of the request of
        every request.'''
        if hasattr(g, 'db'):
            g.db.close()
            g.pop('workspace')
            app.logger.info('Database connection destroyed.')

    from recon.core.web.views import core
    app.register_blueprint(core)
    from recon.core.web.views import resources
    app.register_blueprint(resources)

    return app
