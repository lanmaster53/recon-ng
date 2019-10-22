from dicttoxml import dicttoxml
from flask import current_app, Response, jsonify, send_file, stream_with_context
from io import StringIO
from io import BytesIO
from recon.core.web.utils import add_worksheet, is_url
import os
import requests
import unicodecsv as csv
import xlsxwriter

def _jsonify(rows):
    return jsonify(rows=[dict(r) for r in rows])

def csvify(rows):
    '''Expects a list of dictionaries and returns a CSV response.'''
    if not rows:
        csv_str = ''
    else:
        s = BytesIO()
        keys = rows[0].keys()
        dw = csv.DictWriter(s, keys)
        dw.writeheader()
        dw.writerows([dict(r) for r in rows])
        csv_str = s.getvalue()
    return Response(csv_str, mimetype='text/csv')

def xmlify(rows):
    '''Expects a list of dictionaries and returns a XML response.'''
    xml = dicttoxml([dict(r) for r in rows])
    return Response(xml, mimetype='text/xml')

def listify(rows):
    '''Expects a list of dictionaries and returns a continous list of
    values from all of the provided columns.'''
    columns = {}
    for row in rows:
        for column in row.keys():
            if column not in columns:
                columns[column] = []
            columns[column].append(row[column])
    s = StringIO()
    for column in columns:
        s.write('# '+column+os.linesep)
        for value in columns[column]:
            if type(value) != str:
                value = str(value)
            s.write(value+os.linesep)
    list_str = s.getvalue()
    return Response(list_str, mimetype='text/plain')

def xlsxify(rows):
    '''Expects a list of dictionaries and returns an xlsx response.'''
    sfp = BytesIO()
    with xlsxwriter.Workbook(sfp) as workbook:
        # create a single worksheet for the provided rows
        add_worksheet(workbook, 'worksheet', rows)
    sfp.seek(0)
    return send_file(
        sfp,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        attachment_filename=f"export.xlsx"
    )

# http://flask.pocoo.org/docs/0.12/patterns/streaming/
def proxify(rows):
    @stream_with_context
    def generate():
        '''Expects a list of dictionaries containing URLs and requests them
        through a configured proxy.'''
        # don't bother setting up if there's nothing to process
        if not rows:
            yield 'Nothing to send to proxy.'
        # disable TLS validation warning
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        # set static request options
        kwargs = {
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            },
            'proxies': {
                'http': 'http://127.0.0.1:8080',
                'https': 'http://127.0.0.1:8080',
            },
            'allow_redirects': False,
            'verify': False,
        }
        # process the rows
        for row in [dict(r) for r in rows]:
            for key in row:
                url = row[key]
                msg = f"URL: {url}{os.linesep}Status: "
                if is_url(url):
                    try:
                        resp = requests.request('GET', url, **kwargs)
                        msg += f"HTTP {resp.status_code}: Successfully proxied."
                    except Exception as e:
                        msg += str(e)
                else:
                    msg += 'Error: Failed URL validation.'
                msg += os.linesep*2
                yield msg
    return Response(generate(), mimetype='text/plain')
