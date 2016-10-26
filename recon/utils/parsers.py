from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError
from StringIO import StringIO
from urlparse import urlparse
import lxml.etree
import olefile
import os
import re
import zipfile

def parse_hostname(s):
    host = urlparse(s)
    if not host.scheme:
        host = urlparse('//'+s)
    return host.netloc

def parse_emails(s):
    return re.findall(r'([^\s]+@[^\s]+)', s)

def ole_parser(s):
    ole = olefile.OleFileIO(s)
    meta = ole.get_metadata()
    attrs = meta.DOCSUM_ATTRIBS + meta.SUMMARY_ATTRIBS
    #meta.dump()
    result = {}
    for attr in attrs:
        if hasattr(meta, attr):
            result[attr] = getattr(meta, attr)
    ole.close()
    return result

def ooxml_parser(s):
    zf = zipfile.ZipFile(StringIO(s))
    doc = lxml.etree.fromstring(zf.read('docProps/core.xml'))
    meta = [(x.tag, x.text) for x in doc.xpath('/*/*', namespaces=doc.nsmap)]
    #print(lxml.etree.tostring(doc, pretty_print=True))
    result = {}
    for el in meta:
        result[el[0].split('}')[-1]] = el[1]
    return result

def pdf_parser(s):
    s = s.strip()
    # required to suppress warning messages
    with open(os.devnull, 'w') as fp:
        pdf = PdfFileReader(StringIO(s), strict=False, warndest=fp)
    if pdf.isEncrypted:
        try:
            pdf.decrypt('')
        except NotImplementedError:
            return {}
    meta = pdf.getDocumentInfo()
    #print(str(meta))
    result = {}
    for key in meta.keys():
        result[key[1:]] = meta.get(key)
    return result
