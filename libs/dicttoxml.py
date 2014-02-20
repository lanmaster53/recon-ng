#!/usr/bin/env python
# coding: utf-8

"""
Converts a native Python dictionary into an XML string. Supports int, float, str, unicode, list, dict and arbitrary nesting.
"""

from __future__ import unicode_literals

__version__ = '1.3.1'

from random import randint
import collections
import logging
import sys

# python 3 doesn't have a unicode type
try:
    unicode
except:
    unicode = str

def set_debug(debug=True, filename='dicttoxml.log'):
    if debug:
        print('Debug mode is on. Events are logged at: %s' % (filename))
        logging.basicConfig(filename=filename, level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
        print('Debug mode is off.')

ids = [] # initialize list of unique ids

def make_id(element, start=100000, end=999999):
    """Returns a random integer"""
    return '%s_%s' % (element, randint(start, end))

def get_unique_id(element):
    """Returns a unique id for a given element"""
    this_id = make_id(element)
    dup = True
    while dup == True:
        if this_id not in ids:
            dup = False
            ids.append(this_id)
        else:
            this_id = make_id(element)
    return ids[-1]


def xml_escape(s):
    if type(s) in (str, unicode):
        s = s.replace('&',  '&amp;')
        s = s.replace('"',  '&quot;')
        s = s.replace('\'', '&apos;')
        s = s.replace('<',  '&lt;')
        s = s.replace('>',  '&gt;')
    return s

def make_attrstring(attr):
    """Returns an attribute string in the form key="val" """
    attrstring = ' '.join(['%s="%s"' % (k, v) for k, v in attr.items()])
    return '%s%s' % (' ' if attrstring != '' else '', attrstring)

def convert(obj, ids, parent='root'):
    """Routes the elements of an object to the right function to convert them based on their data type"""
    logging.info('Inside convert(). obj type is: %s' % (type(obj).__name__))
    if type(obj) in (int, float, str, unicode):
        return convert_kv('item', obj)
    if hasattr(obj, 'isoformat'):
        return convert_kv('item', obj.isoformat())
    if type(obj) == bool:
        return convert_bool('item', obj)
    if isinstance(obj, dict):
        return convert_dict(obj, ids, parent)
    if type(obj) in (list, set, tuple) or isinstance(obj, collections.Iterable):
        return convert_list(obj, ids, parent)
    raise TypeError('Unsupported data type: %s (%s)' % (obj, type(obj).__name__))
    
def convert_dict(obj, ids, parent):
    """Converts a dict into an XML string."""
    logging.info('Inside convert_dict(): obj type is: %s' % (type(obj).__name__))
    output = []
    addline = output.append
        
    for k, v in obj.items():
        logging.info('Looping inside convert_dict(): k=%s, type(v)=%s' % (k, type(v).__name__))
        try:
            if k.isdigit():
                k = 'n%s' % (k)
        except:
            if type(k) in (int, float):
                k = 'n%s' % (k)
        this_id = get_unique_id(parent)
        attr = {} if ids == False else {'id': '%s' % (this_id) }
        
        if type(v) in (int, float, str, unicode):
            addline(convert_kv(k, v, attr))
        elif hasattr(v, 'isoformat'): # datetime
            addline(convert_kv(k, v.isoformat(), attr))
        elif type(v) == bool:
            addline(convert_bool(k, v, attr))
        elif isinstance(v, dict):
            addline('<%s type="dict"%s>%s</%s>' % (
                k, make_attrstring(attr), convert_dict(v, ids, k), k)
            )
        elif type(v) in (list, set, tuple) or isinstance(v, collections.Iterable):
            addline('<%s type="list"%s>%s</%s>' % (
                k, make_attrstring(attr), convert_list(v, ids, k), k)
            )
        elif v is None:
            addline('<%s type="null"%s></%s>' % (k, make_attrstring(attr), k))
        else:
            raise TypeError('Unsupported data type: %s (%s)' % (obj, type(obj).__name__))
    return ''.join(output)

def convert_list(items, ids, parent):
    """Converts a list into an XML string."""
    logging.info('Inside convert_list()')
    output = []
    addline = output.append
    this_id = get_unique_id(parent)
    for i, item in enumerate(items):
        logging.info('Looping inside convert_list(): item=%s, type=%s' % (item, type(item).__name__))
        attr = {} if ids == False else {
            'id': '%s_%s' % (this_id, i+1) 
        }
        if type(item) in (int, float, str, unicode):
            addline(convert_kv('item', item, attr))
        elif hasattr(item, 'isoformat'): # datetime
            addline(convert_kv('item', item.isoformat(), attr))
        elif type(item) == bool:
            addline(convert_bool('item', item, attr))
        elif isinstance(item, dict):
            addline('<item type="dict">%s</item>' % (convert_dict(item, ids, parent)))
        elif type(item) in (list, set, tuple) or isinstance(item, collections.Iterable):
            addline('<item type="list"%s>%s</item>' % (make_attrstring(attr), convert_list(item, ids, 'item')))
        else:
            raise TypeError('Unsupported data type: %s (%s)' % (item, type(item).__name__))
    return ''.join(output)

def convert_kv(key, val, attr={}):
    """Converts an int, float or string into an XML element"""
    logging.info('Inside convert_kv(): k=%s, type(v) is: %s' % (key, type(val).__name__))
    attrstring = make_attrstring(attr)
    return '<%s type="%s"%s>%s</%s>' % (
        key, type(val).__name__ if type(val).__name__ != 'unicode' else 'str', 
        attrstring, xml_escape(val), key
    )

def convert_bool(k, v, attr={}):
    """Converts a boolean into an XML element"""
    logging.info('Inside convert_bool(): k=%s, type(v) is: %s' % (k, type(v).__name__))
    attrstring = make_attrstring(attr)
    return '<%s type="bool"%s>%s</%s>' % (k, attrstring, unicode(v).lower(), k)

def dicttoxml(obj, root=True, ids=False):
    """Converts a python object into XML"""
    logging.info('Inside dicttoxml(): type(obj) is: %s' % (type(obj).__name__))
    output = []
    addline = output.append
    if root == True:
        addline('<?xml version="1.0" encoding="UTF-8" ?>')
        addline('<root>%s</root>' % (convert(obj, ids, parent='root')))
    else:
        addline(convert(obj, ids, parent=''))
    return ''.join(output)
