from dicttoxml import dicttoxml
from flask import Response, send_file
from io import BytesIO
from recon.core.web.utils import add_worksheet, debug, is_url, StringIO
from recon.utils import requests
import os
import unicodecsv as csv
import xlsxwriter

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
    xml = dicttoxml(rows)
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
        s.write(u'# '+column+os.linesep)
        for value in columns[column]:
            if type(value) != unicode:
                value = unicode(value)
            s.write(value+os.linesep)
    list_str = s.getvalue()
    return Response(list_str, mimetype='text/plain')

def xlsxify(rows):
    '''Expects a list of dictionaries and returns an xlsx response.'''
    sfp = StringIO()
    with xlsxwriter.Workbook(sfp) as workbook:
        # create a single worksheet for the provided rows
        add_worksheet(workbook, 'worksheet', rows)
    sfp.seek(0)
    return send_file(sfp, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# http://flask.pocoo.org/docs/0.12/patterns/streaming/
def proxify(rows):
    def generate():
        '''Expects a list of dictionaries containing URLs and requests them
        through a configured proxy.'''
        # don't bother setting up if there's nothing to process
        if not rows:
            yield 'Nothing to send to proxy.'
        # build the request object
        req = requests.Request(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
            proxy='127.0.0.1:8080',
            redirect=False,
        )
        # process the rows
        for row in rows:
            for key in row:
                url = unicode(row[key])
                msg = 'URL: '+url+os.linesep+'Status: '
                if is_url(url):
                    try:
                        resp = req.send(url)
                        msg += 'HTTP {}: Successfully proxied.'.format(resp.status_code)
                    except Exception as e:
                        msg += str(e)
                else:
                    msg += 'Error: Failed URL validation.'
                msg += os.linesep*2
                debug(msg.strip())
                yield msg
    return Response(generate(), mimetype='text/plain')
