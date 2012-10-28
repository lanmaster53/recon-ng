import _cmd
# unique to module
import sqlite3
import csv

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'datatype': 'all',
                        'file': './data/results.csv',
                        'verbose': False,
                        }

    def do_info(self, params):
        print ''
        print 'Creates a CSV file containing the specified harvested data types.'
        print ''
        print 'Datatype options: hosts,contacts,all'
        print ''

    def do_run(self, params):
        self.append_to_csv()
    
    def append_to_csv(self):
        try: outfile = open(self.options['file'], 'ab')
        except:
            self.error('Invalid path or filename.')
            return
        verbose = self.options['verbose']
        datatype = self.options['datatype']
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        rows = []
        if datatype == 'hosts': rows = c.execute('SELECT * FROM hosts ORDER BY host').fetchall()
        elif datatype == 'contacts' : rows = c.execute('SELECT * FROM contacts ORDER BY fname').fetchall()
        elif datatype == 'all':
            rows.extend(c.execute('SELECT * FROM hosts ORDER BY host').fetchall())
            rows.extend(c.execute('SELECT * FROM contacts ORDER BY fname').fetchall())
            datatype = 'items'
        else:
            self.error('Invalid output data type.')
        for row in rows:
            row = filter(None, row)
            csvwriter = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            csvwriter.writerow([unicode(s).encode("utf-8") for s in row])
        conn.commit()
        conn.close()
        outfile.close()
        if len(rows) > 0: print '[*] %d %s added to \'%s\'.' % (len(rows), datatype, self.options['file'])