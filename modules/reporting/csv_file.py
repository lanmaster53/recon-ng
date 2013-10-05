import framework
# unique to module
import csv

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'all', 'yes', 'source of data for the report (see \'info\' for options)')
        self.register_option('filename', '%s/results.csv' % (self.workspace), 'yes', 'path and filename for report output')
        self.info = {
                     'Name': 'CSV File Creator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a CSV file containing the specified harvested data types.',
                     'Comments': [
                                  'Source options: [ <table> | all | <sql> ]'
                                  ]
                     }

    def module_run(self):
        # validate that file can be created
        filename = self.options['filename']['value']
        outfile = open(filename, 'w')
        # handle the source of information for the report
        source = self.options['source']['value'].lower()
        rows = []
        tables = [x[0].lower() for x in self.query('SELECT name FROM sqlite_master WHERE type=\'table\'') if x[0] not in ['leaks', 'dashboard']]
        if source in tables:
            rows = self.query('SELECT * FROM "%s" ORDER BY 1' % source)
        elif source == 'all':
            for table in tables:
                rows.extend(self.query('SELECT * FROM "%s" ORDER BY 1' % (table)))
        elif source.startswith('select'):
            rows = self.query(source)
        else:
            self.error('Invalid data source.')
            return
        if not rows:
            self.output('No data returned.')
            return
        cnt = 0
        for row in rows:
            row = [x if x else '' for x in row]
            if any(row):
                cnt += 1
                csvwriter = csv.writer(outfile, quoting=csv.QUOTE_ALL)
                csvwriter.writerow([s.encode("utf-8") for s in row])
        outfile.close()
        self.output('%d records added to \'%s\'.' % (cnt, filename))
