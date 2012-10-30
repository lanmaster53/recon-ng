import _cmd
# unique to module
import sqlite3
import csv

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'source': 'all',
                        'file': './data/results.csv'
                        }

    def do_info(self, params):
        print ''
        print 'Creates a CSV file containing the specified harvested data types.'
        print ''
        print 'Source options: hosts,contacts,all,<sql>'
        print 'Only SELECT queries allowed.'
        print ''

    def do_run(self, params):
        self.append_to_csv()
    
    def append_to_csv(self):
        try: outfile = open(self.options['file'], 'wb')
        except:
            self.error('Invalid path or filename.')
            return
        source = self.options['source']
        conn = sqlite3.connect(self.goptions['dbfilename'])
        c = conn.cursor()
        rows = []
        if source == 'hosts': rows = self.do_query('SELECT * FROM hosts ORDER BY host', True)
        elif source == 'contacts' : rows = self.do_query('SELECT * FROM contacts ORDER BY fname', True)
        elif source == 'all':
            rows.extend(self.do_query('SELECT * FROM hosts ORDER BY host', True))
            rows.extend(self.do_query('SELECT * FROM contacts ORDER BY fname', True))
            # rename source for summary
            source = 'rows'
        elif source.lower().startswith('select'):
            rows = self.do_query(source, True)
            source = 'rows'
        else: self.error('Invalid output data type.')
        for row in rows:
            row = filter(None, row)
            csvwriter = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            csvwriter.writerow([unicode(s).encode("utf-8") for s in row])
        conn.commit()
        conn.close()
        outfile.close()
        print '[*] %d %s added to \'%s\'.' % (len(rows), source, self.options['file'])