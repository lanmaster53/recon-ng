from flask import render_template, send_file
from recon.core.web.utils import add_worksheet, get_tables, query, StringIO
import xlsxwriter

def xlsx():
    '''Returns an xlsx file containing the entire dataset for the current
    workspace.'''
    sfp = StringIO()
    with xlsxwriter.Workbook(sfp) as workbook:
        # create a worksheet for each table in the current workspace
        for table in [t['name'] for t in get_tables()]:
            rows = query('SELECT * FROM {}'.format(table))
            add_worksheet(workbook, table, rows)
    sfp.seek(0)
    return send_file(sfp, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

def pushpin():
    return render_template('pushpin.html')
