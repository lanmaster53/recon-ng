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
        return {
            'modules': sorted(list(recon._loaded_modules.keys())),
        }

api.add_resource(ModuleList, '/modules/')


class ModuleInst(Resource):

    def get(self, module):
        '''Returns information about the provided module.'''
        module = recon._loaded_modules.get(module)
        if module is None:
            abort(404)
        meta = {k: v for k, v in module.meta.items()}
        # provide options with more context
        options = module.options.serialize()
        if options:
            meta['options'] = options
        return meta

    def patch(self, module):
        '''Updates the provided module. Options are the only modifiable
        property of a module object.'''
        module = recon._loaded_modules.get(module)
        if module is None:
            abort(404)
        options = request.json.get('options')
        # process options
        if options:
            for option in options:
                name = option.get('name')
                value = option.get('value')
                if name and value and name in module.options:
                    module.options[name] = value
                    module._save_config(name)
        return self.get(module._modulename)

api.add_resource(ModuleInst, '/modules/<path:module>')


class WorkspaceList(Resource):

    def get(self):
        return {
            'workspaces': sorted(recon._get_workspaces()),
        }

api.add_resource(WorkspaceList, '/workspaces/')


class WorkspaceInst(Resource):

    def get(self, workspace):
        '''Returns information about the provided workspace. Only returns 
        options for the active workspace.'''
        if workspace not in recon._get_workspaces():
            abort(404)
        status = 'inactive'
        options = []
        if workspace == current_app.config['WORKSPACE']:
            status = 'active'
            options = recon.options.serialize()
        return {
            'name': workspace,
            'status': status,
            'options': options,
        }

    def patch(self, workspace):
        '''Updates the provided workspace. When activating a workspace, 
        deactivates the currently activated workspace. Options for inactive 
        workspaces cannot be modified.'''
        if workspace not in recon._get_workspaces():
            abort(404)
        status = request.json.get('status')
        options = request.json.get('options')
        # process status
        if status:
            # ignore everything but a request to activate
            if status == 'active':
                # only continue if the workspace is not already active
                if current_app.config['WORKSPACE'] != workspace:
                    # initialize the workspace
                    recon._init_workspace(workspace)
                    # add the workspace name the to global object
                    current_app.config['WORKSPACE'] = workspace
                    current_app.logger.info(f"Workspace initialized: {workspace}")
        # process options
        if options:
            # only continue if the workspace is active
            if current_app.config['WORKSPACE'] == workspace:
                for option in options:
                    name = option.get('name')
                    value = option.get('value')
                    if name and value and name in recon.options:
                        recon.options[name] = value
                        recon._save_config(name)
        return self.get(workspace)

api.add_resource(WorkspaceInst, '/workspaces/<string:workspace>')


class DashboardInst(Resource):

    def get(self):
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
        # sort both lists in descending order
        records.sort(key=lambda r: r['count'], reverse=True)
        activity.sort(key=lambda m: m['runs'], reverse=True)
        return {
            'workspace': current_app.config['WORKSPACE'],
            'records': records,
            'activity': activity,
        }

api.add_resource(DashboardInst, '/dashboard')


class ReportList(Resource):

    def get(self):
        return {
            'reports': sorted(list(REPORTS.keys())),
        }

api.add_resource(ReportList, '/reports/')


class ReportInst(Resource):

    def get(self, report):
        if report not in REPORTS:
            abort(404)
        return REPORTS[report]()

api.add_resource(ReportInst, '/reports/<string:report>')


class TableList(Resource):

    def get(self):
        return {
            'workspace': current_app.config['WORKSPACE'],
            'tables': sorted(recon.get_tables()),
        }

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
        return {
            'workspace': current_app.config['WORKSPACE'],
            'table': table,
            'columns': columns,
            'rows': rows,
        }

api.add_resource(TableInst, '/tables/<string:table>')


class ExportList(Resource):

    def get(self):
        return {
            'exports': sorted(list(EXPORTS.keys())),
        }

api.add_resource(ExportList, '/exports')
