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
        ),
    }

    def module_run(self):
        filename = self.options['filename']
        # codecs module not used because the csv module converts to ascii
        with open(filename, 'w') as outfile:
            # build a list of table names
            table = self.options['table']
            rows = self.query('SELECT * FROM "%s" ORDER BY 1' % (table))
            cnt = 0
            for row in rows:
                row = [x if x else '' for x in row]
                if any(row):
                    cnt += 1
                    csvwriter = csv.writer(outfile, quoting=csv.QUOTE_ALL)
                    csvwriter.writerow([s.encode("utf-8") for s in row])
        self.output('%d records added to \'%s\'.' % (cnt, filename))
