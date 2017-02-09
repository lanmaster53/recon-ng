from flask import Flask
import os

# print welcome message
welcome = '''\
*************************************************************************
 * Welcome to Recon-web, the analytics and reporting engine for Recon-ng!
 * This is a web-based user interface. Open the following URL in your browser to begin.'''
print welcome

# configuration
DEBUG = False
SECRET_KEY = 'we keep no secrets here.'
HOME_DIR = os.path.join(os.path.expanduser('~'), '.recon-ng')
DATABASE = os.path.join(HOME_DIR, 'workspaces', '{}', 'data.db')
JSON_SORT_KEYS = False

app = Flask(__name__)
app.config.from_object(__name__)

import views
