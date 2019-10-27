from flask import Blueprint, current_app, request, abort
from flask_restful import Resource, Api
from recon.core.web import recon, tasks
from recon.core.web.utils import columnize
from recon.core.web.constants import EXPORTS, REPORTS

resources = Blueprint('resources', __name__, url_prefix='/api')
api = Api()
api.init_app(resources)


class TaskList(Resource):

    def get(self):
        '''
        Gets all tasks for the current workspace
        ---
        responses:
            200:
                description: List of tasks
                schema:
                    properties:
                        tasks:
                            type: array
                            items:
                                $ref: '#/definitions/Task'
                    required:
                    - tasks
        '''
        return {
            'tasks': tasks.get_tasks(),
        }

    def post(self):
        '''
        Runs a module as a background task
        ---
        parameters:
          - name: body
            in: body
            description: Object containing the path of the module to run
            schema:
                properties:
                    path:
                        type: string
                required:
                - path
        responses:
            201:
                description: Object containing the ID of the created task
                schema:
                    properties:
                        task:
                            type: string
                    required:
                    - task
        '''
        path = request.json.get('path')
        if not path or path not in recon._loaded_modules:
            abort(404)
        job = current_app.task_queue.enqueue('recon.core.tasks.run_module', current_app.config['WORKSPACE'], path)
        tid = job.get_id()
        status = job.get_status()
        tasks.add_task(tid, status)
        return {
            'task': tid,
        }, 201

api.add_resource(TaskList, '/tasks/')


class TaskInst(Resource):

    def get(self, tid):
        '''
        Gets the specified task
        ---
        parameters:
          - name: tid
            in: path
            description: ID of the target task
            required: true
            type: string
          - name: live
            in: query
            description: If set, queries the Redis queue instead of the database
            required: false
            type: string
        responses:
            200:
                description: Object containing the specified task
                schema:
                    $ref: '#/definitions/Task'
        '''
        if tid not in tasks.get_ids():
            abort(404)
        # process requests for the rq version of the task
        if request.args.get('live'):
            # baseline task object
            task = {
                'id': tid,
                'status': 'unknown',
                'result': None,
            }
            job = current_app.task_queue.fetch_job(tid)
            if job:
                task['status'] = job.get_status()
                task['result'] = job.result
        else:
            task = tasks.get_task(tid)
        return task

api.add_resource(TaskInst, '/tasks/<string:tid>')


class ModuleList(Resource):

    def get(self):
        '''
        Gets all module names from the framework
        ---
        responses:
            200:
                description: List of module names
                schema:
                    properties:
                        modules:
                            type: array
                            items:
                                type: string
                    required:
                    - modules
        '''
        return {
            'modules': sorted(list(recon._loaded_modules.keys())),
        }

api.add_resource(ModuleList, '/modules/')


class ModuleInst(Resource):

    def get(self, module):
        '''
        Gets information about the specified module
        ---
        parameters:
          - name: module
            in: path
            description: Path of the target module
            required: true
            type: string
        responses:
            200:
                description: Object containing the specified module's information
                schema:
                    $ref: '#/definitions/Module'
        '''
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
        '''
        Updates the specified module
        Options are the only modifiable property of a module object.
        ---
        parameters:
          - name: module
            in: path
            description: Name of the target module
            required: true
            type: string
          - name: body
            in: body
            description: Object containing the options to update
            schema:
                properties:
                    options:
                        type: array
                        items:
                            type: object
                            properties:
                                name:
                                    type: string
                                value:
                                    type: string
                            required:
                            - name
                            - value
                required:
                - options
        responses:
            200:
                description: Object containing the modified module's information
                schema:
                    $ref: '#/definitions/Module'
        '''
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
        '''
        Gets all workspace names from the framework
        ---
        responses:
            200:
                description: List of workspace names
                schema:
                    properties:
                        workspaces:
                            type: array
                            items:
                                type: string
                    required:
                    - workspaces
        '''
        return {
            'workspaces': sorted(recon._get_workspaces()),
        }

api.add_resource(WorkspaceList, '/workspaces/')


class WorkspaceInst(Resource):

    def get(self, workspace):
        '''
        Gets information about the specified workspace
        Only returns options for the active workspace.
        ---
        parameters:
          - name: workspace
            in: path
            description: Name of the target workspace
            required: true
            type: string
        responses:
            200:
                description: Object containing the specified workspace's information
                schema:
                    $ref: '#/definitions/Workspace'
        '''
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
        '''
        Updates the specified workspace
        Activating a workspace deactivates the currently activated workspace, and only the active workspace's options can be modified.
        ---
        parameters:
          - name: workspace
            in: path
            description: Name of the target workspace
            required: true
            type: string
          - name: body
            in: body
            description: Object containing the properties to update
            schema:
                properties:
                    status:
                        type: string
                    options:
                        type: array
                        items:
                            type: object
                            properties:
                                name:
                                    type: string
                                value:
                                    type: string
                            required:
                            - name
                            - value
        responses:
            200:
                description: Object containing the modified workspace's information
                schema:
                    $ref: '#/definitions/Workspace'
        '''
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
                    # re-initialize the workspace and tasks object
                    recon._init_workspace(workspace)
                    tasks.__init__(recon)
                    # add the workspace name the to global object
                    current_app.config['WORKSPACE'] = workspace
                    print((f" * Workspace initialized: {workspace}"))
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
        '''
        Gets summary information about the current workspace
        ---
        responses:
            200:
                description: Object containing the summary information
                schema:
                    $ref: '#/definitions/Dashboard'
        '''
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
        '''
        Gets all report types from the framework
        ---
        responses:
            200:
                description: List of report types
                schema:
                    properties:
                        reports:
                            type: array
                            items:
                                type: string
                    required:
                    - reports
        '''
        return {
            'reports': sorted(list(REPORTS.keys())),
        }

api.add_resource(ReportList, '/reports/')


class ReportInst(Resource):

    def get(self, report):
        '''
        Runs the specified report for the current workspace
        ---
        parameters:
          - name: report
            in: path
            description: Name of the report type
            required: true
            type: string
        '''
        if report not in REPORTS:
            abort(404)
        return REPORTS[report]()

api.add_resource(ReportInst, '/reports/<string:report>')


class TableList(Resource):

    def get(self):
        '''
        Gets all table names for the current workspace
        ---
        responses:
            200:
                description: Object containing the list of tables names
                schema:
                    properties:
                        workspace:
                            type: string
                        tables:
                            type: array
                            items:
                                type: string
                    required:
                    - workspace
                    - tables
        '''
        return {
            'workspace': current_app.config['WORKSPACE'],
            'tables': sorted(recon.get_tables()),
        }

api.add_resource(TableList, '/tables/')


class TableInst(Resource):

    def get(self, table):
        '''
        Dumps the contents of the specified table
        ---
        parameters:
          - name: table
            in: path
            description: Name of the target table
            required: true
            type: string
          - name: format
            in: query
            description: Export type
            required: false
            type: string
        responses:
            200:
                description: Object containing the specified table's contents
                schema:
                    $ref: '#/definitions/Table'
        '''
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
        '''
        Gets all export types from the framework
        ---
        responses:
            200:
                description: List of export types
                schema:
                    properties:
                        exports:
                            type: array
                            items:
                                type: string
                    required:
                    - exports
        '''
        return {
            'exports': sorted(list(EXPORTS.keys())),
        }

api.add_resource(ExportList, '/exports')
