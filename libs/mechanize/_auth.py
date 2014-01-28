"""HTTP Authentication and Proxy support.


Copyright 2006 John J. Lee <jjl@pobox.com>

This code is free software; you can redistribute it and/or modify it under
the terms of the BSD or ZPL 2.1 licenses (see the file COPYING.txt
included with the distribution).

"""

from _urllib2_fork import HTTPPasswordMgr


# TODO: stop deriving from HTTPPasswordMgr
class HTTPProxyPasswordMgr(HTTPPasswordMgr):
    # has default realm and host/port
    def add_password(self, realm, uri, user, passwd):
        # uri could be a single URI or a sequence
        if uri is None or isinstance(uri, basestring):
            uris = [uri]
        else:
            uris = uri
        passwd_by_domain = self.passwd.setdefault(realm, {})
        for uri in uris:
            for default_port in True, False:
                reduced_uri = self.reduce_uri(uri, default_port)
                passwd_by_domain[reduced_uri] = (user, passwd)

    def find_user_password(self, realm, authuri):
        attempts = [(realm, authuri), (None, authuri)]
        # bleh, want default realm to take precedence over default
        # URI/authority, hence this outer loop
        for default_uri in False, True:
            for realm, authuri in attempts:
                authinfo_by_domain = self.passwd.get(realm, {})
                for default_port in True, False:
                    reduced_authuri = self.reduce_uri(authuri, default_port)
                    for uri, authinfo in authinfo_by_domain.iteritems():
                        if uri is None and not default_uri:
                            continue
                        if self.is_suburi(uri, reduced_authuri):
                            return authinfo
                    user, password = None, None

                    if user is not None:
                        break
        return user, password

    def reduce_uri(self, uri, default_port=True):
        if uri is None:
            return None
        return HTTPPasswordMgr.reduce_uri(self, uri, default_port)

    def is_suburi(self, base, test):
        if base is None:
            # default to the proxy's host/port
            hostport, path = test
            base = (hostport, "/")
        return HTTPPasswordMgr.is_suburi(self, base, test)


class HTTPSClientCertMgr(HTTPPasswordMgr):
    # implementation inheritance: this is not a proper subclass
    def add_key_cert(self, uri, key_file, cert_file):
        self.add_password(None, uri, key_file, cert_file)
    def find_key_cert(self, authuri):
        return HTTPPasswordMgr.find_user_password(self, None, authuri)
