"""URL opener.

Copyright 2004-2006 John J Lee <jjl@pobox.com>

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD or ZPL 2.1 licenses (see the file
COPYING.txt included with the distribution).

"""

import os, urllib2, bisect, httplib, types, tempfile
try:
    import threading as _threading
except ImportError:
    import dummy_threading as _threading
try:
    set
except NameError:
    import sets
    set = sets.Set

from _request import Request
import _response
import _rfc3986
import _sockettimeout
import _urllib2_fork
from _util import isstringlike

open_file = open


class ContentTooShortError(urllib2.URLError):
    def __init__(self, reason, result):
        urllib2.URLError.__init__(self, reason)
        self.result = result


def set_request_attr(req, name, value, default):
    try:
        getattr(req, name)
    except AttributeError:
        setattr(req, name, default)
    if value is not default:
        setattr(req, name, value)


class OpenerDirector(_urllib2_fork.OpenerDirector):
    def __init__(self):
        _urllib2_fork.OpenerDirector.__init__(self)
        # really none of these are (sanely) public -- the lack of initial
        # underscore on some is just due to following urllib2
        self.process_response = {}
        self.process_request = {}
        self._any_request = {}
        self._any_response = {}
        self._handler_index_valid = True
        self._tempfiles = []

    def add_handler(self, handler):
        if not hasattr(handler, "add_parent"):
            raise TypeError("expected BaseHandler instance, got %r" %
                            type(handler))

        if handler in self.handlers:
            return
        # XXX why does self.handlers need to be sorted?
        bisect.insort(self.handlers, handler)
        handler.add_parent(self)
        self._handler_index_valid = False

    def _maybe_reindex_handlers(self):
        if self._handler_index_valid:
            return

        handle_error = {}
        handle_open = {}
        process_request = {}
        process_response = {}
        any_request = set()
        any_response = set()
        unwanted = []

        for handler in self.handlers:
            added = False
            for meth in dir(handler):
                if meth in ["redirect_request", "do_open", "proxy_open"]:
                    # oops, coincidental match
                    continue

                if meth == "any_request":
                    any_request.add(handler)
                    added = True
                    continue
                elif meth == "any_response":
                    any_response.add(handler)
                    added = True
                    continue

                ii = meth.find("_")
                scheme = meth[:ii]
                condition = meth[ii+1:]

                if condition.startswith("error"):
                    jj = meth[ii+1:].find("_") + ii + 1
                    kind = meth[jj+1:]
                    try:
                        kind = int(kind)
                    except ValueError:
                        pass
                    lookup = handle_error.setdefault(scheme, {})
                elif condition == "open":
                    kind = scheme
                    lookup = handle_open
                elif condition == "request":
                    kind = scheme
                    lookup = process_request
                elif condition == "response":
                    kind = scheme
                    lookup = process_response
                else:
                    continue

                lookup.setdefault(kind, set()).add(handler)
                added = True

            if not added:
                unwanted.append(handler)

        for handler in unwanted:
            self.handlers.remove(handler)

        # sort indexed methods
        # XXX could be cleaned up
        for lookup in [process_request, process_response]:
            for scheme, handlers in lookup.iteritems():
                lookup[scheme] = handlers
        for scheme, lookup in handle_error.iteritems():
            for code, handlers in lookup.iteritems():
                handlers = list(handlers)
                handlers.sort()
                lookup[code] = handlers
        for scheme, handlers in handle_open.iteritems():
            handlers = list(handlers)
            handlers.sort()
            handle_open[scheme] = handlers

        # cache the indexes
        self.handle_error = handle_error
        self.handle_open = handle_open
        self.process_request = process_request
        self.process_response = process_response
        self._any_request = any_request
        self._any_response = any_response

    def _request(self, url_or_req, data, visit,
                 timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT):
        if isstringlike(url_or_req):
            req = Request(url_or_req, data, visit=visit, timeout=timeout)
        else:
            # already a mechanize.Request instance
            req = url_or_req
            if data is not None:
                req.add_data(data)
            # XXX yuck
            set_request_attr(req, "visit", visit, None)
            set_request_attr(req, "timeout", timeout,
                             _sockettimeout._GLOBAL_DEFAULT_TIMEOUT)
        return req

    def open(self, fullurl, data=None,
             timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT):
        req = self._request(fullurl, data, None, timeout)
        req_scheme = req.get_type()

        self._maybe_reindex_handlers()

        # pre-process request
        # XXX should we allow a Processor to change the URL scheme
        #   of the request?
        request_processors = set(self.process_request.get(req_scheme, []))
        request_processors.update(self._any_request)
        request_processors = list(request_processors)
        request_processors.sort()
        for processor in request_processors:
            for meth_name in ["any_request", req_scheme+"_request"]:
                meth = getattr(processor, meth_name, None)
                if meth:
                    req = meth(req)

        # In Python >= 2.4, .open() supports processors already, so we must
        # call ._open() instead.
        urlopen = _urllib2_fork.OpenerDirector._open
        response = urlopen(self, req, data)

        # post-process response
        response_processors = set(self.process_response.get(req_scheme, []))
        response_processors.update(self._any_response)
        response_processors = list(response_processors)
        response_processors.sort()
        for processor in response_processors:
            for meth_name in ["any_response", req_scheme+"_response"]:
                meth = getattr(processor, meth_name, None)
                if meth:
                    response = meth(req, response)

        return response

    def error(self, proto, *args):
        if proto in ['http', 'https']:
            # XXX http[s] protocols are special-cased
            dict = self.handle_error['http'] # https is not different than http
            proto = args[2]  # YUCK!
            meth_name = 'http_error_%s' % proto
            http_err = 1
            orig_args = args
        else:
            dict = self.handle_error
            meth_name = proto + '_error'
            http_err = 0
        args = (dict, proto, meth_name) + args
        result = apply(self._call_chain, args)
        if result:
            return result

        if http_err:
            args = (dict, 'default', 'http_error_default') + orig_args
            return apply(self._call_chain, args)

    BLOCK_SIZE = 1024*8
    def retrieve(self, fullurl, filename=None, reporthook=None, data=None,
                 timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT,
                 open=open_file):
        """Returns (filename, headers).

        For remote objects, the default filename will refer to a temporary
        file.  Temporary files are removed when the OpenerDirector.close()
        method is called.

        For file: URLs, at present the returned filename is None.  This may
        change in future.

        If the actual number of bytes read is less than indicated by the
        Content-Length header, raises ContentTooShortError (a URLError
        subclass).  The exception's .result attribute contains the (filename,
        headers) that would have been returned.

        """
        req = self._request(fullurl, data, False, timeout)
        scheme = req.get_type()
        fp = self.open(req)
        try:
            headers = fp.info()
            if filename is None and scheme == 'file':
                # XXX req.get_selector() seems broken here, return None,
                #   pending sanity :-/
                return None, headers
                #return urllib.url2pathname(req.get_selector()), headers
            if filename:
                tfp = open(filename, 'wb')
            else:
                path = _rfc3986.urlsplit(req.get_full_url())[2]
                suffix = os.path.splitext(path)[1]
                fd, filename = tempfile.mkstemp(suffix)
                self._tempfiles.append(filename)
                tfp = os.fdopen(fd, 'wb')
            try:
                result = filename, headers
                bs = self.BLOCK_SIZE
                size = -1
                read = 0
                blocknum = 0
                if reporthook:
                    if "content-length" in headers:
                        size = int(headers["Content-Length"])
                    reporthook(blocknum, bs, size)
                while 1:
                    block = fp.read(bs)
                    if block == "":
                        break
                    read += len(block)
                    tfp.write(block)
                    blocknum += 1
                    if reporthook:
                        reporthook(blocknum, bs, size)
            finally:
                tfp.close()
        finally:
            fp.close()

        # raise exception if actual size does not match content-length header
        if size >= 0 and read < size:
            raise ContentTooShortError(
                "retrieval incomplete: "
                "got only %i out of %i bytes" % (read, size),
                result
                )

        return result

    def close(self):
        _urllib2_fork.OpenerDirector.close(self)

        # make it very obvious this object is no longer supposed to be used
        self.open = self.error = self.retrieve = self.add_handler = None

        if self._tempfiles:
            for filename in self._tempfiles:
                try:
                    os.unlink(filename)
                except OSError:
                    pass
            del self._tempfiles[:]


def wrapped_open(urlopen, process_response_object, fullurl, data=None,
                 timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT):
    success = True
    try:
        response = urlopen(fullurl, data, timeout)
    except urllib2.HTTPError, error:
        success = False
        if error.fp is None:  # not a response
            raise
        response = error

    if response is not None:
        response = process_response_object(response)

    if not success:
        raise response
    return response

class ResponseProcessingOpener(OpenerDirector):

    def open(self, fullurl, data=None,
             timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT):
        def bound_open(fullurl, data=None,
                       timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT):
            return OpenerDirector.open(self, fullurl, data, timeout)
        return wrapped_open(
            bound_open, self.process_response_object, fullurl, data, timeout)

    def process_response_object(self, response):
        return response


class SeekableResponseOpener(ResponseProcessingOpener):
    def process_response_object(self, response):
        return _response.seek_wrapped_response(response)


def isclass(obj):
    return isinstance(obj, (types.ClassType, type))


class OpenerFactory:
    """This class's interface is quite likely to change."""

    default_classes = [
        # handlers
        _urllib2_fork.ProxyHandler,
        _urllib2_fork.UnknownHandler,
        _urllib2_fork.HTTPHandler,
        _urllib2_fork.HTTPDefaultErrorHandler,
        _urllib2_fork.HTTPRedirectHandler,
        _urllib2_fork.FTPHandler,
        _urllib2_fork.FileHandler,
        # processors
        _urllib2_fork.HTTPCookieProcessor,
        _urllib2_fork.HTTPErrorProcessor,
        ]
    if hasattr(httplib, 'HTTPS'):
        default_classes.append(_urllib2_fork.HTTPSHandler)
    handlers = []
    replacement_handlers = []

    def __init__(self, klass=OpenerDirector):
        self.klass = klass

    def build_opener(self, *handlers):
        """Create an opener object from a list of handlers and processors.

        The opener will use several default handlers and processors, including
        support for HTTP and FTP.

        If any of the handlers passed as arguments are subclasses of the
        default handlers, the default handlers will not be used.

        """
        opener = self.klass()
        default_classes = list(self.default_classes)
        skip = set()
        for klass in default_classes:
            for check in handlers:
                if isclass(check):
                    if issubclass(check, klass):
                        skip.add(klass)
                elif isinstance(check, klass):
                    skip.add(klass)
        for klass in skip:
            default_classes.remove(klass)

        for klass in default_classes:
            opener.add_handler(klass())
        for h in handlers:
            if isclass(h):
                h = h()
            opener.add_handler(h)

        return opener


build_opener = OpenerFactory().build_opener

_opener = None
urlopen_lock = _threading.Lock()
def urlopen(url, data=None, timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT):
    global _opener
    if _opener is None:
        urlopen_lock.acquire()
        try:
            if _opener is None:
                _opener = build_opener()
        finally:
            urlopen_lock.release()
    return _opener.open(url, data, timeout)

def urlretrieve(url, filename=None, reporthook=None, data=None,
                timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT):
    global _opener
    if _opener is None:
        urlopen_lock.acquire()
        try:
            if _opener is None:
                _opener = build_opener()
        finally:
            urlopen_lock.release()
    return _opener.retrieve(url, filename, reporthook, data, timeout)

def install_opener(opener):
    global _opener
    _opener = opener
