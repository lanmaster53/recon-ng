from flask import current_app, send_file, Response, render_template
from io import BytesIO
from recon.core.web import recon
from recon.core.web.utils import columnize, add_worksheet
import xlsxwriter

def xlsx():
    '''Returns an xlsx file containing the entire dataset for the current
    workspace.'''
    sfp = BytesIO()
    with xlsxwriter.Workbook(sfp) as workbook:
        # create a worksheet for each table in the current workspace
        for table in recon.get_tables():
            rows = recon.query(f"SELECT * FROM {table}", include_header=True)
            columns = rows.pop(0)
            rows = columnize(columns, rows)
            add_worksheet(workbook, table, rows)
    sfp.seek(0)
    return send_file(
        sfp,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        attachment_filename=f"{current_app.config['WORKSPACE']}.xlsx"
    )

def pushpin():
    google_api_key = recon.get_key('google_api')
    return Response(render_template('pushpin.html', api_key=google_api_key), mimetype='text/html')
