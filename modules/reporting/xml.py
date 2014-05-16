import module
# unique to module
import codecs
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('filename', '%s/results.xml' % (self.workspace), 'yes', 'path and filename for report output')
        self.register_option('tables', 'hosts, contacts, creds', 'yes', 'comma delineated list of tables')
        self.info = {
                     'Name': 'XML Report Generator',
                     'Author': 'Eric Humphries (@e2fsck) and Tim Tomes (@LaNMaSteR53)',
                     'Version': 'v0.0.2',
                     'Description': 'Creates a XML report.',
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
            columns = [x[1] for x in self.query('PRAGMA table_info(\'%s\')' % (table))]
            rows = self.query('SELECT "%s" FROM "%s" ORDER BY 1' % ('", "'.join(columns), table))
            for row in rows:
                row_dict = {}
                for i in range(0,len(columns)):
                    row_dict[columns[i]] = row[i]
                data_dict[table].append(row_dict)
                cnt += 1

        # write the xml to a file
        reparsed = parseString(dicttoxml(data_dict))
        outfile.write(reparsed.toprettyxml(indent=' '*4))
        outfile.close()

        self.output('%d records added to \'%s\'.' % (cnt, filename))
