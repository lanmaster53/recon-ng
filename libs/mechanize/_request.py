"""Integration with Python standard library module urllib2: Request class.

Copyright 2004-2006 John J Lee <jjl@pobox.com>

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD or ZPL 2.1 licenses (see the file
COPYING.txt included with the distribution).

"""

import logging

import _rfc3986
import _sockettimeout
import _urllib2_fork

warn = logging.getLogger("mechanize").warning


class Request(_urllib2_fork.Request):
    def __init__(self, url, data=None, headers={},
                 origin_req_host=None, unverifiable=False, visit=None,
                 timeout=_sockettimeout._GLOBAL_DEFAULT_TIMEOUT):
        # In mechanize 0.2, the interpretation of a unicode url argument will
        # change: A unicode url argument will be interpreted as an IRI, and a
        # bytestring as a URI. For now, we accept unicode or bytestring.  We
        # don't insist that the value is always a URI (specifically, must only
        # contain characters which are legal), because that might break working
        # code (who knows what bytes some servers want to see, especially with
        # browser plugins for internationalised URIs).
        if not _rfc3986.is_clean_uri(url):
            warn("url argument is not a URI "
                 "(contains illegal characters) %r" % url)
        _urllib2_fork.Request.__init__(self, url, data, headers)
        self.selector = None
        self.visit = visit
        self.timeout = timeout

    def __str__(self):
        return "<Request for %s>" % self.get_full_url()
