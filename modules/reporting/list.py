from recon.core.module import BaseModule
import codecs
import os

class Module(BaseModule):

    meta = {
        'name': 'List Creator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Creates a file containing a list of records from the database.',
        'options': (
            ('table', 'hosts', True, 'source table of data for the list'),
            ('column', 'ip_address', True, 'source column of data for the list'),
            ('unique', True, True, 'only return unique items from the dataset'),
            ('nulls', False, True, 'include nulls in the dataset'),
            ('filename', os.path.join(BaseModule.workspace, 'list.txt'), True, 'path and filename for output'),
        ),
    }

    def module_run(self):
        filename = self.options['filename']
        with codecs.open(filename, 'wb', encoding='utf-8') as outfile:
            # handle the source of information for the report
            column = self.options['column']
            table = self.options['table']
            nulls = ' WHERE "%s" IS NOT NULL' % (column) if not self.options['nulls'] else ''
            unique = 'DISTINCT ' if self.options['unique'] else ''
            values = (unique, column, table, nulls)
            query = 'SELECT %s"%s" FROM "%s"%s ORDER BY 1' % values
            rows = self.query(query)
            for row in [x[0] for x in rows]:
                row = row if row else ''
                outfile.write('%s\n' % (row))
                print(row)
        self.output('%d items added to \'%s\'.' % (len(rows), filename))
