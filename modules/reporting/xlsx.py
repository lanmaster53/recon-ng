import module
# unique to module
import xlsxwriter

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('filename', '%s/results.xlsx' % (self.workspace), True, 'path and filename for output')
        self.info = {
            'Name': 'XLSX File Creator',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Creates an Excel compatible XLSX file containing the entire data set.'
        }

    def module_run(self):
        filename = self.options['filename']
        # create an new xlsx file
        workbook = xlsxwriter.Workbook(filename)
        tables = self.get_tables()
        # loop through all tables in the database
        for table in tables:
            # create a worksheet for the table
            worksheet = workbook.add_worksheet(table)
            # build the data set
            rows = [tuple([x[0] for x in self.get_columns(table)])]
            rows.extend(self.query('SELECT * FROM "%s"' % (table)))
            # write the rows of data to the xlsx file
            for r in range(0, len(rows)):
                for c in range(0, len(rows[r])):
                    worksheet.write(r, c, rows[r][c])
        workbook.close()
        self.output('All data written to \'%s\'.' % (filename))
