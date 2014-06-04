import module
# unique to module
import codecs

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('table', 'hosts', 'yes', 'source table of data for the list')
        self.register_option('column', 'ip_address', 'yes', 'source column of data for the list')
        self.register_option('unique', True, 'yes', 'only return unique items from the dataset')
        self.register_option('nulls', False, 'yes', 'include nulls in the dataset')
        self.register_option('filename', '%s/list.txt' % (self.workspace), 'yes', 'path and filename for output')
        self.info = {
                     'Name': 'List Creator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a file containing a list of records from the database.'
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
