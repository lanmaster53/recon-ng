from flask import Blueprint, current_app, jsonify, render_template, request
from flask_restful import Resource, Api
from recon.core.web.utils import get_workspaces, get_tables, get_columns, query
from recon.core.web.exports import _jsonify, csvify, xmlify, listify, xlsxify, proxify
from recon.core.web.reports import pushpin, xlsx

EXPORTS = {
    'json': _jsonify,
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

core = Blueprint('core', __name__)

@core.route('/')
def index():
    return render_template('index.html', workspaces=get_workspaces())

resources = Blueprint('resources', __name__, url_prefix='/api')
api = Api()
api.init_app(resources)

class WorkspaceInst(Resource):

    def get(self, workspace):
        # dynamically determine and call reporting function
        report = request.args.get('report')
        if report and report in REPORTS:
            return REPORTS[report]()
        # build the summary data
        tables = [dict(t) for t in get_tables()]
        dashboard = query('SELECT * FROM dashboard')
        modules = [dict(r) for r in dashboard]
        records = []
        for table in tables:
            name = table['name']
            count = query(f"SELECT COUNT(*) AS 'COUNT' FROM {name}")
            records.append({'name': name, 'count':count[0]['COUNT']})
        summary = {
            'records': sorted(records, key=lambda r: r['count'], reverse=True),
            'modules': sorted(modules, key=lambda m: m['runs'], reverse=True),
        }
        return jsonify(tables=tables, summary=summary, reports=list(REPORTS.keys()))

api.add_resource(WorkspaceInst, '/workspaces/<string:workspace>')

class TableInst(Resource):

    def get(self, workspace, table):
        # filter rows for columns if needed
        columns = request.values.get('columns')
        if columns:
            rows = query(f"SELECT {columns} FROM {table}")
        else:
            rows = query(f"SELECT * FROM {table}")
        # dynamically determine and call export function
        _format = request.args.get('format')
        if _format and _format in EXPORTS:
            # any required serialization is handled at the exporter level
            return EXPORTS[_format](rows=rows)
        return jsonify(rows=[dict(r) for r in rows], columns=get_columns(table), exports=list(EXPORTS.keys()))

api.add_resource(TableInst, '/workspaces/<string:workspace>/tables/<string:table>')
