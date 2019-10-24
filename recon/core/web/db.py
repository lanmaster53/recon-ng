from recon.core.web.utils import columnize
import json
import os

class Tasks(object):

    def __init__(self, recon):
        self.recon = recon
        self.path = os.path.join(self.recon.workspace, 'tasks.db')
        if not os.path.exists(self.path):
            self._create_db()

    def query(self, *args, **kwargs):
        return self.recon._query(self.path, *args, **kwargs)

    def _create_db(self):
        self.query('''\
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                PRIMARY KEY (id)
            )'''
        )

    def get_tasks(self):
        tasks = []
        task_ids = [x[0] for x in self.query('SELECT id FROM tasks')]
        for task_id in task_ids:
            tasks.append(self.get_task(task_id))
        return tasks

    def get_ids(self):
        return [t['id'] for t in self.get_tasks()]

    def add_task(self, tid, status, result=None):
        if result:
            result = json.dumps(result)
        return self.query(
            'INSERT INTO tasks (id, status, result) VALUES (?, ?, ?)',
            values=(tid, status, result),
        )

    def get_task(self, tid):
        rows = self.query(
            'SELECT * FROM tasks WHERE id=?',
            values=(tid,),
            include_header=True,
        )
        columns = rows.pop(0)
        task = columnize(columns, rows)[0]
        if task['result']:
            task['result'] = json.loads(task['result'])
        return task

    def update_task(self, tid, **kwargs):
        if kwargs.get('result'):
            kwargs['result'] = json.dumps(kwargs['result'])
        set_items = []
        set_values = []
        for key, value in kwargs.items():
            if kwargs[key]:
                set_items.append(key+'=?')
                set_values.append(value)
        set_str = ', '.join(set_items)
        set_values.append(tid)
        return self.query(
            'UPDATE tasks SET {} WHERE id=?'.format(set_str),
            values=set_values,
        )
