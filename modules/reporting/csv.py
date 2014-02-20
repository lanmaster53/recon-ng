import module
# unique to module
import csv

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('filename', '%s/results.csv' % (self.workspace), 'yes', 'path and filename for report output')
        self.register_option('tables', 'hosts, contacts, creds', 'yes', 'comma delineated list of tables')
        self.info = {
                     'Name': 'CSV File Creator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Creates a CSV file containing the specified harvested data types.',
                     'Comments': []
                     }

    def module_run(self):
        # validate that the file can be created
        filename = self.options['filename']
        outfile = open(filename, 'w')

        # build a list of table names
        tables = [x.strip() for x in self.options['tables'].split(',')]

        rows = []
        for table in tables:
            rows.extend(self.query('SELECT * FROM "%s" ORDER BY 1' % (table)))
        cnt = 0
        for row in rows:
            row = [x if x else '' for x in row]
            if any(row):
                cnt += 1
                csvwriter = csv.writer(outfile, quoting=csv.QUOTE_ALL)
                csvwriter.writerow([s.encode("utf-8") for s in row])
        outfile.close()

        self.output('%d records added to \'%s\'.' % (cnt, filename))
