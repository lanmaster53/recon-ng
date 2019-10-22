from flask import Blueprint, current_app, render_template, request, abort
from flask_restful import Resource, Api
from recon.core.web import recon
from recon.core.web.utils import columnize
from recon.core.web.constants import EXPORTS, REPORTS

core = Blueprint('core', __name__)

@core.route('/')
def index():
    return render_template('index.html', workspaces=recon._get_workspaces())

resources = Blueprint('resources', __name__, url_prefix='/api')
api = Api()
api.init_app(resources)


class ModuleList(Resource):

    def get(self):
        return list(recon._loaded_modules.keys())

api.add_resource(ModuleList, '/modules/')


class ModuleInst(Resource):

    def get(self, module):
        module = recon._loaded_modules.get(module)
        if module is None:
            abort(404)
        return {k: v for k, v in module.meta.items()}

api.add_resource(ModuleInst, '/modules/<path:module>')


class WorkspaceList(Resource):

    def get(self):
        return recon._get_workspaces()

api.add_resource(WorkspaceList, '/workspaces/')


class WorkspaceInst(Resource):

    def get(self, workspace):
        if workspace not in recon._get_workspaces():
            abort(404)
        # initialize the workspace if not already
        if current_app.config['WORKSPACE'] != workspace:
            # put the recon object in the right workspace
            recon._init_workspace(workspace)
            # add the workspace name the to global object
            current_app.config['WORKSPACE'] = workspace
            current_app.logger.info(f"Workspace initialized: {workspace}")
        # build the activity object
        dashboard = recon.query('SELECT * FROM dashboard', include_header=True)
        columns = dashboard.pop(0)
        activity = columnize(columns, dashboard)
        # build the records object
        records = []
        tables = recon.get_tables()
        for table in tables:
            count = recon.query(f"SELECT COUNT(*) AS 'COUNT' FROM {table}")
            records.append({'name': table, 'count':count[0][0]})
        records.sort(key=lambda r: r['count'], reverse=True)
        activity.sort(key=lambda m: m['runs'], reverse=True)
        return {'records': records, 'activity': activity}

api.add_resource(WorkspaceInst, '/workspaces/<string:workspace>')


class ReportsList(Resource):

    def get(self):
        return list(REPORTS.keys())

api.add_resource(ReportsList, '/reports/')


class ReportsInst(Resource):

    def get(self, report):
        if report not in REPORTS:
            abort(404)
        return REPORTS[report]()

api.add_resource(ReportsInst, '/reports/<string:report>')


class TableList(Resource):

    def get(self):
        return recon.get_tables()

api.add_resource(TableList, '/tables/')


class TableInst(Resource):

    def get(self, table):
        if table not in recon.get_tables():
            abort(404)
        # filter rows for columns if needed
        columns = request.values.get('columns')
        if columns:
            rows = recon.query(f"SELECT {columns} FROM {table}", include_header=True)
        else:
            rows = recon.query(f"SELECT * FROM {table}", include_header=True)
        columns = rows.pop(0)
        rows = columnize(columns, rows)
        # dynamically determine and call export function
        _format = request.args.get('format')
        if _format and _format in EXPORTS:
            # any required serialization is handled at the exporter level
            return EXPORTS[_format](rows=rows)
        return {'columns': columns, 'rows': rows}

api.add_resource(TableInst, '/tables/<string:table>')

class ExportsList(Resource):

    def get(self):
        return list(EXPORTS.keys())

api.add_resource(ExportsList, '/exports')
