"""Firefox 3 "cookies.sqlite" cookie persistence.

Copyright 2008 John J Lee <jjl@pobox.com>

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD or ZPL 2.1 licenses (see the file
COPYING.txt included with the distribution).

"""

import logging
import time

from _clientcookie import CookieJar, Cookie, MappingIterator
from _util import isstringlike, experimental
debug = logging.getLogger("mechanize.cookies").debug


class Firefox3CookieJar(CookieJar):

    """Firefox 3 cookie jar.

    The cookies are stored in Firefox 3's "cookies.sqlite" format.

    Constructor arguments:

    filename: filename of cookies.sqlite (typically found at the top level
     of a firefox profile directory)
    autoconnect: as a convenience, connect to the SQLite cookies database at
     Firefox3CookieJar construction time (default True)
    policy: an object satisfying the mechanize.CookiePolicy interface

    Note that this is NOT a FileCookieJar, and there are no .load(),
    .save() or .restore() methods.  The database is in sync with the
    cookiejar object's state after each public method call.

    Following Firefox's own behaviour, session cookies are never saved to
    the database.

    The file is created, and an sqlite database written to it, if it does
    not already exist. The moz_cookies database table is created if it does
    not already exist.
    """

    # XXX
    # handle DatabaseError exceptions
    # add a FileCookieJar (explicit .save() / .revert() / .load() methods)

    def __init__(self, filename, autoconnect=True, policy=None):
        experimental("Firefox3CookieJar is experimental code")
        CookieJar.__init__(self, policy)
        if filename is not None and not isstringlike(filename):
            raise ValueError("filename must be string-like")
        self.filename = filename
        self._conn = None
        if autoconnect:
            self.connect()

    def connect(self):
        import sqlite3  # not available in Python 2.4 stdlib
        self._conn = sqlite3.connect(self.filename)
        self._conn.isolation_level = "DEFERRED"
        self._create_table_if_necessary()

    def close(self):
        self._conn.close()

    def _transaction(self, func):
        try:
            cur = self._conn.cursor()
            try:
                result = func(cur)
            finally:
                cur.close()
        except:
            self._conn.rollback()
            raise
        else:
            self._conn.commit()
        return result

    def _execute(self, query, params=()):
        return self._transaction(lambda cur: cur.execute(query, params))

    def _query(self, query, params=()):
        # XXX should we bother with a transaction?
        cur = self._conn.cursor()
        try:
            cur.execute(query, params)
            return cur.fetchall()
        finally:
            cur.close()

    def _create_table_if_necessary(self):
        self._execute("""\
CREATE TABLE IF NOT EXISTS moz_cookies (id INTEGER PRIMARY KEY, name TEXT,
    value TEXT, host TEXT, path TEXT,expiry INTEGER,
    lastAccessed INTEGER, isSecure INTEGER, isHttpOnly INTEGER)""")

    def _cookie_from_row(self, row):
        (pk, name, value, domain, path, expires,
         last_accessed, secure, http_only) = row

        version = 0
        domain = domain.encode("ascii", "ignore")
        path = path.encode("ascii", "ignore")
        name = name.encode("ascii", "ignore")
        value = value.encode("ascii", "ignore")
        secure = bool(secure)

        # last_accessed isn't a cookie attribute, so isn't added to rest
        rest = {}
        if http_only:
            rest["HttpOnly"] = None

        if name == "":
            name = value
            value = None

        initial_dot = domain.startswith(".")
        domain_specified = initial_dot

        discard = False
        if expires == "":
            expires = None
            discard = True

        return Cookie(version, name, value,
                      None, False,
                      domain, domain_specified, initial_dot,
                      path, False,
                      secure,
                      expires,
                      discard,
                      None,
                      None,
                      rest)

    def clear(self, domain=None, path=None, name=None):
        CookieJar.clear(self, domain, path, name)
        where_parts = []
        sql_params = []
        if domain is not None:
            where_parts.append("host = ?")
            sql_params.append(domain)
            if path is not None:
                where_parts.append("path = ?")
                sql_params.append(path)
                if name is not None:
                    where_parts.append("name = ?")
                    sql_params.append(name)
        where = " AND ".join(where_parts)
        if where:
            where = " WHERE " + where
        def clear(cur):
            cur.execute("DELETE FROM moz_cookies%s" % where,
                        tuple(sql_params))
        self._transaction(clear)

    def _row_from_cookie(self, cookie, cur):
        expires = cookie.expires
        if cookie.discard:
            expires = ""

        domain = unicode(cookie.domain)
        path = unicode(cookie.path)
        name = unicode(cookie.name)
        value = unicode(cookie.value)
        secure = bool(int(cookie.secure))

        if value is None:
            value = name
            name = ""

        last_accessed = int(time.time())
        http_only = cookie.has_nonstandard_attr("HttpOnly")

        query = cur.execute("""SELECT MAX(id) + 1 from moz_cookies""")
        pk = query.fetchone()[0]
        if pk is None:
            pk = 1

        return (pk, name, value, domain, path, expires,
                last_accessed, secure, http_only)

    def set_cookie(self, cookie):
        if cookie.discard:
            CookieJar.set_cookie(self, cookie)
            return

        def set_cookie(cur):
            # XXX
            # is this RFC 2965-correct?
            # could this do an UPDATE instead?
            row = self._row_from_cookie(cookie, cur)
            name, unused, domain, path = row[1:5]
            cur.execute("""\
DELETE FROM moz_cookies WHERE host = ? AND path = ? AND name = ?""",
                        (domain, path, name))
            cur.execute("""\
INSERT INTO moz_cookies VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", row)
        self._transaction(set_cookie)

    def __iter__(self):
        # session (non-persistent) cookies
        for cookie in MappingIterator(self._cookies):
            yield cookie
        # persistent cookies
        for row in self._query("""\
SELECT * FROM moz_cookies ORDER BY name, path, host"""):
            yield self._cookie_from_row(row)

    def _cookies_for_request(self, request):
        session_cookies = CookieJar._cookies_for_request(self, request)
        def get_cookies(cur):
            query = cur.execute("SELECT host from moz_cookies")
            domains = [row[0] for row in query.fetchall()]
            cookies = []
            for domain in domains:
                cookies += self._persistent_cookies_for_domain(domain,
                                                               request, cur)
            return cookies
        persistent_coookies = self._transaction(get_cookies)
        return session_cookies + persistent_coookies

    def _persistent_cookies_for_domain(self, domain, request, cur):
        cookies = []
        if not self._policy.domain_return_ok(domain, request):
            return []
        debug("Checking %s for cookies to return", domain)
        query = cur.execute("""\
SELECT * from moz_cookies WHERE host = ? ORDER BY path""",
                            (domain,))
        cookies = [self._cookie_from_row(row) for row in query.fetchall()]
        last_path = None
        r = []
        for cookie in cookies:
            if (cookie.path != last_path and
                not self._policy.path_return_ok(cookie.path, request)):
                last_path = cookie.path
                continue
            if not self._policy.return_ok(cookie, request):
                debug("   not returning cookie")
                continue
            debug("   it's a match")
            r.append(cookie)
        return r
