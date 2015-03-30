from recon.core.module import BaseModule
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString
import codecs
import os

class Module(BaseModule):

    meta = {
        'name': 'XML Report Generator',
        'author': 'Eric Humphries (@e2fsck) and Tim Tomes (@LaNMaSteR53)',
        'version': 'v0.0.2',
        'description': 'Creates a XML report.',
        'options': (
            ('tables', 'hosts, contacts, credentials', True, 'comma delineated list of tables'),
            ('filename', os.path.join(BaseModule.workspace, 'results.xml'), True, 'path and filename for report output'),
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
            # write the xml to a file
            reparsed = parseString(dicttoxml(data_dict))
            outfile.write(reparsed.toprettyxml(indent=' '*4))
        self.output('%d records added to \'%s\'.' % (cnt, filename))
