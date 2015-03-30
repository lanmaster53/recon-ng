from recon.core.module import BaseModule
import codecs
import json
import os

class Module(BaseModule):

    meta = {
        'name': 'JSON Report Generator',
        'author': 'Paul (@PaulWebSec)',
        'version': 'v0.0.1',
        'description': 'Creates a JSON report.',
        'options': (
            ('tables', 'hosts, contacts, credentials', True, 'comma delineated list of tables'),
            ('filename', os.path.join(BaseModule.workspace, 'results.json'), True, 'path and filename for report output'),
        ),
    }

    def module_run(self):
        filename = self.options['filename']
        with codecs.open(filename, 'wb', encoding='utf-8') as outfile:
            # build a list of table names
            tables = [x.strip() for x in self.options['tables'].split(',')]
            data_dict = {}
            cnt = 0
            for table in tables:
                data_dict[table] = []
                columns = [x[0] for x in self.get_columns(table)]
                rows = self.query('SELECT "%s" FROM "%s" ORDER BY 1' % ('", "'.join(columns), table))
                for row in rows:
                    row_dict = {}
                    for i in range(0,len(columns)):
                        row_dict[columns[i]] = row[i]
                    data_dict[table].append(row_dict)
                    cnt += 1
            # write the JSON to a file
            outfile.write(json.dumps(data_dict, indent=4))
        self.output('%d records added to \'%s\'.' % (cnt, filename))
