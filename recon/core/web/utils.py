from flask import g, current_app
from sqlite3 import dbapi2 as sqlite3
import os
import re

def columnize(columns, rows):
    return [{columns[i]: row[i] for i in range(0, len(columns))} for row in rows]

def add_worksheet(workbook, name, rows):
    '''Helper function for building xlsx files.'''
    worksheet = workbook.add_worksheet(name)
    # build the data set
    if rows:
        _rows = [list(rows[0].keys())]
        for row in rows:
            _row = []
            for key in _rows[0]:
                _row.append(row[key])
            _rows.append(_row)
        # write the rows of data to the xlsx file
        for r in range(0, len(_rows)):
            for c in range(0, len(_rows[r])):
                worksheet.write(r, c, _rows[r][c])

def is_url(s):
    if type(s) not in (str, bytes):
        return False
    ip_middle_octet = r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5]))"
    ip_last_octet = r"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
    regex = re.compile(
        r"^"
        # protocol identifier
        r"(?:(?:https?|ftp)://)"
        # user:pass authentication
        r"(?:\S+(?::\S*)?@)?"
        r"(?:"
        r"(?P<private_ip>"
        # IP address exclusion
        # private & local networks
        r"(?:(?:10|127)" + ip_middle_octet + "{2}" + ip_last_octet + ")|"
        r"(?:(?:169\.254|192\.168)" + ip_middle_octet + ip_last_octet + ")|"
        r"(?:172\.(?:1[6-9]|2\d|3[0-1])" + ip_middle_octet + ip_last_octet + "))"
        r"|"
        # IP address dotted notation octets
        # excludes loopback network 0.0.0.0
        # excludes reserved space >= 224.0.0.0
        # excludes network & broadcast addresses
        # (first & last IP address of each class)
        r"(?P<public_ip>"
        r"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
        r"" + ip_middle_octet + "{2}"
        r"" + ip_last_octet + ")"
        r"|"
        # host name
        r"(?:(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)"
        # domain name
        r"(?:\.(?:[a-z\u00a1-\uffff0-9]-?)*[a-z\u00a1-\uffff0-9]+)*"
        # TLD identifier
        r"(?:\.(?:[a-z\u00a1-\uffff]{2,}))"
        r")"
        # port number
        r"(?::\d{2,5})?"
        # resource path
        r"(?:/\S*)?"
        # query string
        r"(?:\?\S*)?"
        r"$",
        re.UNICODE | re.IGNORECASE
    )
    pattern = re.compile(regex)
    if pattern.match(s):
        return True
    return False
