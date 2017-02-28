from flask import g, session
from recon.core.web import app
from sqlite3 import dbapi2 as sqlite3
import os
import re

# import statement to be leveraged by other modules
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

def debug(str):
    if app.config['DEBUG']:
        for line in str.split('\n'):
            print('[DEBUG] '+line)

def get_workspaces():
    dirnames = []
    path = os.path.join(app.config['HOME_DIR'], 'workspaces')
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            dirnames.append(name)
    return dirnames

def get_tables():
    tables = query('SELECT name FROM sqlite_master WHERE type=\'table\'')
    return sorted(tables, key=lambda t: t['name'])

def get_columns(table):
    return [x[1] for x in query('PRAGMA table_info(\'{}\')'.format(table))]

def connect_db():
    '''Connects to the specific database.'''
    rv = sqlite3.connect(session['database'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    '''Opens a new database connection if there is none yet for the
    current application context.'''
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
        debug('Database connection created.')
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    '''Closes the database again at the end of the request.'''
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
        debug('Database connection destroyed.')

def query(query, values=()):
    '''Queries the database and returns the results as a list.'''
    db = get_db()
    debug('Query: {}'.format(query))
    if values:
        cur = db.execute(query, values)
    else:
        cur = db.execute(query)
    return cur.fetchall()

def add_worksheet(workbook, name, rows):
    '''Helper function for building xlsx files.'''
    worksheet = workbook.add_worksheet(name)
    # build the data set
    if rows:
        _rows = [rows[0].keys()]
        for row in rows:
            _row = []
            for key in _rows[0]:
                _row.append(row[key])
            _rows.append(_row)
        # write the rows of data to the xlsx file
        for r in range(0, len(_rows)):
            for c in range(0, len(_rows[r])):
                worksheet.write(r, c, _rows[r][c])

def is_url(s):
    ip_middle_octet = u"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5]))"
    ip_last_octet = u"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
    regex = re.compile(
        u"^"
        # protocol identifier
        u"(?:(?:https?|ftp)://)"
        # user:pass authentication
        u"(?:\S+(?::\S*)?@)?"
        u"(?:"
        u"(?P<private_ip>"
        # IP address exclusion
        # private & local networks
        u"(?:(?:10|127)" + ip_middle_octet + u"{2}" + ip_last_octet + u")|"
        u"(?:(?:169\.254|192\.168)" + ip_middle_octet + ip_last_octet + u")|"
        u"(?:172\.(?:1[6-9]|2\d|3[0-1])" + ip_middle_octet + ip_last_octet + u"))"
        u"|"
        # IP address dotted notation octets
        # excludes loopback network 0.0.0.0
        # excludes reserved space >= 224.0.0.0
        # excludes network & broadcast addresses
        # (first & last IP address of each class)
        u"(?P<public_ip>"
        u"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
        u"" + ip_middle_octet + u"{2}"
        u"" + ip_last_octet + u")"
        u"|"
        # host name
        u"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
        # domain name
        u"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
        # TLD identifier
        u"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
        u")"
        # port number
        u"(?::\d{2,5})?"
        # resource path
        u"(?:/\S*)?"
        # query string
        u"(?:\?\S*)?"
        u"$",
        re.UNICODE | re.IGNORECASE
    )
    pattern = re.compile(regex)
    if pattern.match(s):
        return True
    return False
