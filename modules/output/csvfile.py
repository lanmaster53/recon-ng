import _cmd
# unique to module
import sqlite3
import csv

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'items': 'hosts',
                        'file': './data/results.csv',
                        'verbose': False,
                        }

    def do_info(self, params):
        print ''
        print 'Creates a CSV file containing the specified harvested items.'
        print ''

    def do_run(self, params):
        self.append_to_csv()
    
    def append_to_csv(self):
        outfile = open(self.options['file'], 'ab')
        verbose = self.options['verbose']
        conn = sqlite3.connect(self.dbfilename)
        c = conn.cursor()
        if self.options['items'] == 'hosts': rows = c.execute('SELECT * FROM hosts ORDER BY host').fetchall()
        elif self.options['items'] == 'contacts': rows = c.execute('SELECT * FROM contacts ORDER BY fname').fetchall()
        else:
            self.default('Invalid output items.')
            rows = []
        for row in rows:
            csvwriter = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            csvwriter.writerow(row)
        conn.commit()
        conn.close()
        outfile.close()
        print '[*] %d %s Added to \'%s\'.' % (len(rows), self.options['items'], self.options['file'])