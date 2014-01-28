"""HTTP related handlers.

Note that some other HTTP handlers live in more specific modules: _auth.py,
_gzip.py, etc.


Copyright 2002-2006 John J Lee <jjl@pobox.com>

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD or ZPL 2.1 licenses (see the file
COPYING.txt included with the distribution).

"""

import HTMLParser
from cStringIO import StringIO
import htmlentitydefs
import logging
import robotparser
import socket
import time

import _sgmllib_copy as sgmllib
from _urllib2_fork import HTTPError, BaseHandler

from _headersutil import is_html
from _html import unescape, unescape_charref
from _request import Request
from _response import response_seek_wrapper
import _rfc3986
import _sockettimeout

debug = logging.getLogger("mechanize").debug
debug_robots = logging.getLogger("mechanize.robots").debug

# monkeypatch urllib2.HTTPError to show URL
## import urllib2
## def urllib2_str(self):
##     return 'HTTP Error %s: %s (%s)' % (
##         self.code, self.msg, self.geturl())
## urllib2.HTTPError.__str__ = urllib2_str


CHUNK = 1024  # size of chunks fed to HTML HEAD parser, in bytes
DEFAULT_ENCODING = 'latin-1'

# XXX would self.reset() work, instead of raising this exception?
class EndOfHeadError(Exception): pass
class AbstractHeadParser:
    # only these elements are allowed in or before HEAD of document
    head_elems = ("html", "head",
                  "title", "base",
                  "script", "style", "meta", "link", "object")
    _entitydefs = htmlentitydefs.name2codepoint
    _encoding = DEFAULT_ENCODING

    def __init__(self):
        self.http_equiv = []

    def start_meta(self, attrs):
        http_equiv = content = None
        for key, value in attrs:
            if key == "http-equiv":
                http_equiv = self.unescape_attr_if_required(value)
            elif key == "content":
                content = self.unescape_attr_if_required(value)
        if http_equiv is not None and content is not None:
            self.http_equiv.append((http_equiv, content))

    def end_head(self):
        raise EndOfHeadError()

    def handle_entityref(self, name):
        #debug("%s", name)
        self.handle_data(unescape(
            '&%s;' % name, self._entitydefs, self._encoding))

    def handle_charref(self, name):
        #debug("%s", name)
        self.handle_data(unescape_charref(name, self._encoding))

    def unescape_attr(self, name):
        #debug("%s", name)
        return unescape(name, self._entitydefs, self._encoding)

    def unescape_attrs(self, attrs):
        #debug("%s", attrs)
        escaped_attrs = {}
        for key, val in attrs.items():
            escaped_attrs[key] = self.unescape_attr(val)
        return escaped_attrs

    def unknown_entityref(self, ref):
        self.handle_data("&%s;" % ref)

    def unknown_charref(self, ref):
        self.handle_data("&#%s;" % ref)


class XHTMLCompatibleHeadParser(AbstractHeadParser,
                                HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        AbstractHeadParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag not in self.head_elems:
            raise EndOfHeadError()
        try:
            method = getattr(self, 'start_' + tag)
        except AttributeError:
            try:
                method = getattr(self, 'do_' + tag)
            except AttributeError:
                pass # unknown tag
            else:
                method(attrs)
        else:
            method(attrs)

    def handle_endtag(self, tag):
        if tag not in self.head_elems:
            raise EndOfHeadError()
        try:
            method = getattr(self, 'end_' + tag)
        except AttributeError:
            pass # unknown tag
        else:
            method()

    def unescape(self, name):
        # Use the entitydefs passed into constructor, not
        # HTMLParser.HTMLParser's entitydefs.
        return self.unescape_attr(name)

    def unescape_attr_if_required(self, name):
        return name  # HTMLParser.HTMLParser already did it

class HeadParser(AbstractHeadParser, sgmllib.SGMLParser):

    def _not_called(self):
        assert False

    def __init__(self):
        sgmllib.SGMLParser.__init__(self)
        AbstractHeadParser.__init__(self)

    def handle_starttag(self, tag, method, attrs):
        if tag not in self.head_elems:
            raise EndOfHeadError()
        if tag == "meta":
            method(attrs)

    def unknown_starttag(self, tag, attrs):
        self.handle_starttag(tag, self._not_called, attrs)

    def handle_endtag(self, tag, method):
        if tag in self.head_elems:
            method()
        else:
            raise EndOfHeadError()

    def unescape_attr_if_required(self, name):
        return self.unescape_attr(name)

def parse_head(fileobj, parser):
    """Return a list of key, value pairs."""
    while 1:
        data = fileobj.read(CHUNK)
        try:
            parser.feed(data)
        except EndOfHeadError:
            break
        if len(data) != CHUNK:
            # this should only happen if there is no HTML body, or if
            # CHUNK is big
            break
    return parser.http_equiv

class HTTPEquivProcessor(BaseHandler):
    """Append META HTTP-EQUIV headers to regular HTTP headers."""

    handler_order = 300  # before handlers that look at HTTP headers

    def __init__(self, head_parser_class=HeadParser,
                 i_want_broken_xhtml_support=False,
                 ):
        self.head_parser_class = head_parser_class
        self._allow_xhtml = i_want_broken_xhtml_support

    def http_response(self, request, response):
        if not hasattr(response, "seek"):
            response = response_seek_wrapper(response)
        http_message = response.info()
        url = response.geturl()
        ct_hdrs = http_message.getheaders("content-type")
        if is_html(ct_hdrs, url, self._allow_xhtml):
            try:
                try:
                    html_headers = parse_head(response,
                                              self.head_parser_class())
                finally:
                    response.seek(0)
            except (HTMLParser.HTMLParseError,
                    sgmllib.SGMLParseError):
                pass
            else:
                for hdr, val in html_headers:
                    # add a header
                    http_message.dict[hdr.lower()] = val
                    text = hdr + ": " + val
                    for line in text.split("\n"):
                        http_message.headers.append(line + "\n")
        return response

    https_response = http_response


class MechanizeRobotFileParser(robotparser.RobotFileParser):

    def __init__(self, url='', opener=None):
        robotparser.RobotFileParser.__init__(self, url)
        self._opener = opener
        self._timeout = _sockettimeout._GLOBAL_DEFAULT_TIMEOUT

    def set_opener(self, opener=None):
        import _opener
        if opener is None:
            opener = _opener.OpenerDirector()
        self._opener = opener

    def set_timeout(self, timeout):
        self._timeout = timeout

    def read(self):
        """Reads the robots.txt URL and feeds it to the parser."""
        if self._opener is None:
            self.set_opener()
        req = Request(self.url, unverifiable=True, visit=False,
                      timeout=self._timeout)
        try:
            f = self._opener.open(req)
        except HTTPError, f:
            pass
        except (IOError, socket.error, OSError), exc:
            debug_robots("ignoring error opening %r: %s" %
                               (self.url, exc))
            return
        lines = []
        line = f.readline()
        while line:
            lines.append(line.strip())
            line = f.readline()
        status = f.code
        if status == 401 or status == 403:
            self.disallow_all = True
            debug_robots("disallow all")
        elif status >= 400:
            self.allow_all = True
            debug_robots("allow all")
        elif status == 200 and lines:
            debug_robots("parse lines")
            self.parse(lines)

class RobotExclusionError(HTTPError):
    def __init__(self, request, *args):
        apply(HTTPError.__init__, (self,)+args)
        self.request = request

class HTTPRobotRulesProcessor(BaseHandler):
    # before redirections, after everything else
    handler_order = 800

    try:
        from httplib import HTTPMessage
    except:
        from mimetools import Message
        http_response_class = Message
    else:
        http_response_class = HTTPMessage

    def __init__(self, rfp_class=MechanizeRobotFileParser):
        self.rfp_class = rfp_class
        self.rfp = None
        self._host = None

    def http_request(self, request):
        scheme = request.get_type()
        if scheme not in ["http", "https"]:
            # robots exclusion only applies to HTTP
            return request

        if request.get_selector() == "/robots.txt":
            # /robots.txt is always OK to fetch
            return request

        host = request.get_host()

        # robots.txt requests don't need to be allowed by robots.txt :-)
        origin_req = getattr(request, "_origin_req", None)
        if (origin_req is not None and
            origin_req.get_selector() == "/robots.txt" and
            origin_req.get_host() == host
            ):
            return request

        if host != self._host:
            self.rfp = self.rfp_class()
            try:
                self.rfp.set_opener(self.parent)
            except AttributeError:
                debug("%r instance does not support set_opener" %
                      self.rfp.__class__)
            self.rfp.set_url(scheme+"://"+host+"/robots.txt")
            self.rfp.set_timeout(request.timeout)
            self.rfp.read()
            self._host = host

        ua = request.get_header("User-agent", "")
        if self.rfp.can_fetch(ua, request.get_full_url()):
            return request
        else:
            # XXX This should really have raised URLError.  Too late now...
            msg = "request disallowed by robots.txt"
            raise RobotExclusionError(
                request,
                request.get_full_url(),
                403, msg,
                self.http_response_class(StringIO()), StringIO(msg))

    https_request = http_request

class HTTPRefererProcessor(BaseHandler):
    """Add Referer header to requests.

    This only makes sense if you use each RefererProcessor for a single
    chain of requests only (so, for example, if you use a single
    HTTPRefererProcessor to fetch a series of URLs extracted from a single
    page, this will break).

    There's a proper implementation of this in mechanize.Browser.

    """
    def __init__(self):
        self.referer = None

    def http_request(self, request):
        if ((self.referer is not None) and
            not request.has_header("Referer")):
            request.add_unredirected_header("Referer", self.referer)
        return request

    def http_response(self, request, response):
        self.referer = response.geturl()
        return response

    https_request = http_request
    https_response = http_response


def clean_refresh_url(url):
    # e.g. Firefox 1.5 does (something like) this
    if ((url.startswith('"') and url.endswith('"')) or
        (url.startswith("'") and url.endswith("'"))):
        url = url[1:-1]
    return _rfc3986.clean_url(url, "latin-1")  # XXX encoding

def parse_refresh_header(refresh):
    """
    >>> parse_refresh_header("1; url=http://example.com/")
    (1.0, 'http://example.com/')
    >>> parse_refresh_header("1; url='http://example.com/'")
    (1.0, 'http://example.com/')
    >>> parse_refresh_header("1")
    (1.0, None)
    >>> parse_refresh_header("blah")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ValueError: invalid literal for float(): blah

    """

    ii = refresh.find(";")
    if ii != -1:
        pause, newurl_spec = float(refresh[:ii]), refresh[ii+1:]
        jj = newurl_spec.find("=")
        key = None
        if jj != -1:
            key, newurl = newurl_spec[:jj], newurl_spec[jj+1:]
            newurl = clean_refresh_url(newurl)
        if key is None or key.strip().lower() != "url":
            raise ValueError()
    else:
        pause, newurl = float(refresh), None
    return pause, newurl

class HTTPRefreshProcessor(BaseHandler):
    """Perform HTTP Refresh redirections.

    Note that if a non-200 HTTP code has occurred (for example, a 30x
    redirect), this processor will do nothing.

    By default, only zero-time Refresh headers are redirected.  Use the
    max_time attribute / constructor argument to allow Refresh with longer
    pauses.  Use the honor_time attribute / constructor argument to control
    whether the requested pause is honoured (with a time.sleep()) or
    skipped in favour of immediate redirection.

    Public attributes:

    max_time: see above
    honor_time: see above

    """
    handler_order = 1000

    def __init__(self, max_time=0, honor_time=True):
        self.max_time = max_time
        self.honor_time = honor_time
        self._sleep = time.sleep

    def http_response(self, request, response):
        code, msg, hdrs = response.code, response.msg, response.info()

        if code == 200 and hdrs.has_key("refresh"):
            refresh = hdrs.getheaders("refresh")[0]
            try:
                pause, newurl = parse_refresh_header(refresh)
            except ValueError:
                debug("bad Refresh header: %r" % refresh)
                return response

            if newurl is None:
                newurl = response.geturl()
            if (self.max_time is None) or (pause <= self.max_time):
                if pause > 1E-3 and self.honor_time:
                    self._sleep(pause)
                hdrs["location"] = newurl
                # hardcoded http is NOT a bug
                response = self.parent.error(
                    "http", request, response,
                    "refresh", msg, hdrs)
            else:
                debug("Refresh header ignored: %r" % refresh)

        return response

    https_response = http_response
