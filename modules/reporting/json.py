import module
# unique to module
import codecs
import json

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('filename', '%s/results.json' % (self.workspace), True, 'path and filename for report output')
        self.register_option('tables', 'hosts, contacts, credentials', True, 'comma delineated list of tables')
        self.info = {
                     'Name': 'JSON Report Generator',
                     'Author': 'Paul (@PaulWebSec)',
                     'Version': 'v0.0.1',
                     'Description': 'Creates a JSON report.',
                     }

    def module_run(self):
        # validate that the file can be created
        filename = self.options['filename']
        outfile = codecs.open(filename, 'wb', encoding='utf-8')

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
        outfile.close()

        self.output('%d records added to \'%s\'.' % (cnt, filename))
