from flask import jsonify, render_template, request, session
from recon.core.web import app
from recon.core.web.utils import get_workspaces, get_tables, get_columns, query
from recon.core.web.exports import csvify, xmlify, listify, xlsxify, proxify
from recon.core.web.reports import pushpin, xlsx

EXPORTS = {
    'json': jsonify,
    'xml': xmlify,
    'csv': csvify,
    'list': listify,
    'xlsx': xlsxify,
    'proxy': proxify,
}

REPORTS = {
    'pushpin': pushpin,
    'xlsx': xlsx,
}

@app.route('/')
def index():
    return render_template('index.html', workspaces=get_workspaces())

@app.route('/api/workspaces/<string:workspace>')
@app.route('/api/workspaces/<string:workspace>.<string:report>')
def api_workspace(workspace, report=''):
    # set/update session data for the current workspace
    session['database'] = app.config['DATABASE'].format(workspace)
    session['workspace'] = workspace
    # dynamically determine and call reporting function
    if report and report in REPORTS:
        return REPORTS[report]()
    # build the summary data
    tables = [dict(t) for t in get_tables()]
    dashboard = query('SELECT * FROM dashboard')
    modules = [dict(r) for r in dashboard]
    records = []
    for table in tables:
        name = table['name']
        count = query('SELECT COUNT(*) AS \'COUNT\' FROM {}'.format(name))
        records.append({'name': name, 'count':count[0]['COUNT']})
    summary = {
        'records': sorted(records, key=lambda r: r['count'], reverse=True),
        'modules': sorted(modules, key=lambda m: m['runs'], reverse=True),
    }
    return jsonify(tables=tables, summary=summary, reports=REPORTS.keys())

@app.route('/api/workspaces/<string:workspace>/tables/<string:table>')
@app.route('/api/workspaces/<string:workspace>/tables/<string:table>.<string:format>')
def api_table(workspace, table, format=''):
    # filter rows for columns if needed
    columns = request.values.get('columns')
    if columns:
        rows = query('SELECT {} FROM {}'.format(columns, table))
    else:
        rows = query('SELECT * FROM {}'.format(table))
    # dynamically determine and call export function
    if format and format in EXPORTS:
        return EXPORTS[format](rows=[dict(r) for r in rows])
    return jsonify(rows=[dict(r) for r in rows], columns=get_columns(table), exports=EXPORTS.keys())
