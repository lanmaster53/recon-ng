from recon.core.module import BaseModule
import csv
import os

class Module(BaseModule):

    meta = {
        'name': 'CSV File Creator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Creates a CSV file containing the specified harvested data.',
        'options': (
            ('table', 'hosts', True, 'source table of data to export'),
            ('filename', os.path.join(BaseModule.workspace, 'results.csv'), True, 'path and filename for output'),
            ('headers', False, True, 'include column headers'),
        ),
    }

    def module_run(self):
        filename = self.options['filename']
        # codecs module not used because the csv module converts to ascii
        with open(filename, 'w') as outfile:
            table = self.options['table']
            csvwriter = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            if self.options['headers']:
                columns = [c[0] for c in self.get_columns(table)]
                csvwriter.writerow(columns)
            cnt = 0
            rows = self.query('SELECT * FROM "%s" ORDER BY 1' % (table))
            for row in rows:
                row = [x if x else '' for x in row]
                if any(row):
                    cnt += 1
                    csvwriter.writerow([s.encode("utf-8") for s in row])
        self.output('%d records added to \'%s\'.' % (cnt, filename))
