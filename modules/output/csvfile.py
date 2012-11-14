import framework
# unique to module
import csv

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'source': 'all',
                        'filename': './data/results.csv'
                        }
        self.info = {
                     'Name': 'CSV File Creator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a CSV file containing the specified harvested data types.',
                     'Comments': [
                                  'Source options: hosts, contacts, creds, all, <sql>'
                                  ]
                     }

    def do_run(self, params):
        self.append_to_csv()
    
    def append_to_csv(self):
        filename = self.options['filename']
        try:
            outfile = open(filename, 'wb')
            outfile.close()
        except:
            self.error('Invalid path or filename.')
            return
        source = self.options['source']
        rows = []
        if source == 'hosts': rows = self.query('SELECT * FROM hosts ORDER BY host')
        elif source == 'contacts' : rows = self.query('SELECT * FROM contacts ORDER BY fname')
        elif source == 'creds' : rows = self.query('SELECT * FROM creds ORDER BY username')
        elif source == 'all':
            rows.extend(self.query('SELECT * FROM hosts ORDER BY host'))
            rows.extend(self.query('SELECT * FROM contacts ORDER BY fname'))
            rows.extend(self.query('SELECT * FROM creds ORDER BY username'))
            # rename source for summary
            source = 'rows'
        elif source.lower().startswith('select'):
            rows = self.query(source)
            source = 'rows'
        else:
            self.error('Invalid data source.')
            return
        outfile = open(filename, 'wb')
        for row in rows:
            row = filter(None, row)
            csvwriter = csv.writer(outfile, quoting=csv.QUOTE_ALL)
            csvwriter.writerow([unicode(s).encode("utf-8") for s in row])
        outfile.close()
        self.output('%d %s added to \'%s\'.' % (len(rows), source, filename))