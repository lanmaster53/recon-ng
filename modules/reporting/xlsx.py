from recon.core.module import BaseModule
import os
import xlsxwriter

class Module(BaseModule):

    meta = {
        'name': 'XLSX File Creator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Creates an Excel compatible XLSX file containing the entire data set.',
        'options': (
            ('filename', os.path.join(BaseModule.workspace, 'results.xlsx'), True, 'path and filename for output'),
        ),
    }

    def module_run(self):
        filename = self.options['filename']
        # create an new xlsx file
        with xlsxwriter.Workbook(filename, {'strings_to_urls': False}) as workbook:
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
        self.output('All data written to \'%s\'.' % (filename))
