from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError
from StringIO import StringIO
import lxml.etree
import olefile
import os
import zipfile

def ole_parser(s):
    ole = olefile.OleFileIO(s)
    meta = ole.get_metadata()
    #meta.dump()
    result = {
        'author': meta.author,
        'last saved by': meta.last_saved_by,
        'company': meta.company,
    }
    ole.close()
    return result

def ooxml_parser(s):
    zf = zipfile.ZipFile(StringIO(s))
    doc = lxml.etree.fromstring(zf.read('docProps/core.xml'))
    #print(lxml.etree.tostring(doc, pretty_print=True))
    result = {
        'creator': ' '.join([x.text for x in doc.xpath('//dc:creator', namespaces=doc.nsmap)]),
        'last modified by': ' '.join([x.text for x in doc.xpath('//cp:lastModifiedBy', namespaces=doc.nsmap)]),
    }
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
    result = {
        'author': meta.author,
    }
    return result
