"""HTML handling.

Copyright 2003-2006 John J. Lee <jjl@pobox.com>

This code is free software; you can redistribute it and/or modify it under
the terms of the BSD or ZPL 2.1 licenses (see the file COPYING.txt
included with the distribution).

"""

import codecs
import copy
import htmlentitydefs
import re

import _sgmllib_copy as sgmllib

import _beautifulsoup
import _form
from _headersutil import split_header_words, is_html as _is_html
import _request
import _rfc3986

DEFAULT_ENCODING = "latin-1"

COMPRESS_RE = re.compile(r"\s+")


class CachingGeneratorFunction(object):
    """Caching wrapper around a no-arguments iterable."""

    def __init__(self, iterable):
        self._cache = []
        # wrap iterable to make it non-restartable (otherwise, repeated
        # __call__ would give incorrect results)
        self._iterator = iter(iterable)

    def __call__(self):
        cache = self._cache
        for item in cache:
            yield item
        for item in self._iterator:
            cache.append(item)
            yield item


class EncodingFinder:
    def __init__(self, default_encoding):
        self._default_encoding = default_encoding
    def encoding(self, response):
        # HTTPEquivProcessor may be in use, so both HTTP and HTTP-EQUIV
        # headers may be in the response.  HTTP-EQUIV headers come last,
        # so try in order from first to last.
        for ct in response.info().getheaders("content-type"):
            for k, v in split_header_words([ct])[0]:
                if k == "charset":
                    encoding = v
                    try:
                        codecs.lookup(v)
                    except LookupError:
                        continue
                    else:
                        return encoding
        return self._default_encoding


class ResponseTypeFinder:
    def __init__(self, allow_xhtml):
        self._allow_xhtml = allow_xhtml
    def is_html(self, response, encoding):
        ct_hdrs = response.info().getheaders("content-type")
        url = response.geturl()
        # XXX encoding
        return _is_html(ct_hdrs, url, self._allow_xhtml)


class Args(object):

    # idea for this argument-processing trick is from Peter Otten

    def __init__(self, args_map):
        self.__dict__["dictionary"] = dict(args_map)

    def __getattr__(self, key):
        try:
            return self.dictionary[key]
        except KeyError:
            return getattr(self.__class__, key)

    def __setattr__(self, key, value):
        if key == "dictionary":
            raise AttributeError()
        self.dictionary[key] = value


def form_parser_args(
    select_default=False,
    form_parser_class=None,
    request_class=None,
    backwards_compat=False,
    ):
    return Args(locals())


class Link:
    def __init__(self, base_url, url, text, tag, attrs):
        assert None not in [url, tag, attrs]
        self.base_url = base_url
        self.absolute_url = _rfc3986.urljoin(base_url, url)
        self.url, self.text, self.tag, self.attrs = url, text, tag, attrs
    def __cmp__(self, other):
        try:
            for name in "url", "text", "tag", "attrs":
                if getattr(self, name) != getattr(other, name):
                    return -1
        except AttributeError:
            return -1
        return 0
    def __repr__(self):
        return "Link(base_url=%r, url=%r, text=%r, tag=%r, attrs=%r)" % (
            self.base_url, self.url, self.text, self.tag, self.attrs)


class LinksFactory:

    def __init__(self,
                 link_parser_class=None,
                 link_class=Link,
                 urltags=None,
                 ):
        import _pullparser
        if link_parser_class is None:
            link_parser_class = _pullparser.TolerantPullParser
        self.link_parser_class = link_parser_class
        self.link_class = link_class
        if urltags is None:
            urltags = {
                "a": "href",
                "area": "href",
                "frame": "src",
                "iframe": "src",
                }
        self.urltags = urltags
        self._response = None
        self._encoding = None

    def set_response(self, response, base_url, encoding):
        self._response = response
        self._encoding = encoding
        self._base_url = base_url

    def links(self):
        """Return an iterator that provides links of the document."""
        response = self._response
        encoding = self._encoding
        base_url = self._base_url
        p = self.link_parser_class(response, encoding=encoding)

        try:
            for token in p.tags(*(self.urltags.keys()+["base"])):
                if token.type == "endtag":
                    continue
                if token.data == "base":
                    base_href = dict(token.attrs).get("href")
                    if base_href is not None:
                        base_url = base_href
                    continue
                attrs = dict(token.attrs)
                tag = token.data
                text = None
                # XXX use attr_encoding for ref'd doc if that doc does not
                #  provide one by other means
                #attr_encoding = attrs.get("charset")
                url = attrs.get(self.urltags[tag])  # XXX is "" a valid URL?
                if not url:
                    # Probably an <A NAME="blah"> link or <AREA NOHREF...>.
                    # For our purposes a link is something with a URL, so
                    # ignore this.
                    continue

                url = _rfc3986.clean_url(url, encoding)
                if tag == "a":
                    if token.type != "startendtag":
                        # hmm, this'd break if end tag is missing
                        text = p.get_compressed_text(("endtag", tag))
                    # but this doesn't work for e.g.
                    # <a href="blah"><b>Andy</b></a>
                    #text = p.get_compressed_text()

                yield Link(base_url, url, text, tag, token.attrs)
        except sgmllib.SGMLParseError, exc:
            raise _form.ParseError(exc)

class FormsFactory:

    """Makes a sequence of objects satisfying HTMLForm interface.

    After calling .forms(), the .global_form attribute is a form object
    containing all controls not a descendant of any FORM element.

    For constructor argument docs, see ParseResponse argument docs.
    """

    def __init__(self,
                 select_default=False,
                 form_parser_class=None,
                 request_class=None,
                 backwards_compat=False,
                 ):
        self.select_default = select_default
        if form_parser_class is None:
            form_parser_class = _form.FormParser
        self.form_parser_class = form_parser_class
        if request_class is None:
            request_class = _request.Request
        self.request_class = request_class
        self.backwards_compat = backwards_compat
        self._response = None
        self.encoding = None
        self.global_form = None

    def set_response(self, response, encoding):
        self._response = response
        self.encoding = encoding
        self.global_form = None

    def forms(self):
        encoding = self.encoding
        forms = _form.ParseResponseEx(
            self._response,
            select_default=self.select_default,
            form_parser_class=self.form_parser_class,
            request_class=self.request_class,
            encoding=encoding,
            _urljoin=_rfc3986.urljoin,
            _urlparse=_rfc3986.urlsplit,
            _urlunparse=_rfc3986.urlunsplit,
            )
        self.global_form = forms[0]
        return forms[1:]

class TitleFactory:
    def __init__(self):
        self._response = self._encoding = None

    def set_response(self, response, encoding):
        self._response = response
        self._encoding = encoding

    def _get_title_text(self, parser):
        import _pullparser
        text = []
        tok = None
        while 1:
            try:
                tok = parser.get_token()
            except _pullparser.NoMoreTokensError:
                break
            if tok.type == "data":
                text.append(str(tok))
            elif tok.type == "entityref":
                t = unescape("&%s;" % tok.data,
                             parser._entitydefs, parser.encoding)
                text.append(t)
            elif tok.type == "charref":
                t = unescape_charref(tok.data, parser.encoding)
                text.append(t)
            elif tok.type in ["starttag", "endtag", "startendtag"]:
                tag_name = tok.data
                if tok.type == "endtag" and tag_name == "title":
                    break
                text.append(str(tok))
        return COMPRESS_RE.sub(" ", "".join(text).strip())

    def title(self):
        import _pullparser
        p = _pullparser.TolerantPullParser(
            self._response, encoding=self._encoding)
        try:
            try:
                p.get_tag("title")
            except _pullparser.NoMoreTokensError:
                return None
            else:
                return self._get_title_text(p)
        except sgmllib.SGMLParseError, exc:
            raise _form.ParseError(exc)


def unescape(data, entities, encoding):
    if data is None or "&" not in data:
        return data

    def replace_entities(match):
        ent = match.group()
        if ent[1] == "#":
            return unescape_charref(ent[2:-1], encoding)

        repl = entities.get(ent[1:-1])
        if repl is not None:
            repl = unichr(repl)
            if type(repl) != type(""):
                try:
                    repl = repl.encode(encoding)
                except UnicodeError:
                    repl = ent
        else:
            repl = ent
        return repl

    return re.sub(r"&#?[A-Za-z0-9]+?;", replace_entities, data)

def unescape_charref(data, encoding):
    name, base = data, 10
    if name.startswith("x"):
        name, base= name[1:], 16
    uc = unichr(int(name, base))
    if encoding is None:
        return uc
    else:
        try:
            repl = uc.encode(encoding)
        except UnicodeError:
            repl = "&#%s;" % data
        return repl


class MechanizeBs(_beautifulsoup.BeautifulSoup):
    _entitydefs = htmlentitydefs.name2codepoint
    # don't want the magic Microsoft-char workaround
    PARSER_MASSAGE = [(re.compile('(<[^<>]*)/>'),
                       lambda(x):x.group(1) + ' />'),
                      (re.compile('<!\s+([^<>]*)>'),
                       lambda(x):'<!' + x.group(1) + '>')
                      ]

    def __init__(self, encoding, text=None, avoidParserProblems=True,
                 initialTextIsEverything=True):
        self._encoding = encoding
        _beautifulsoup.BeautifulSoup.__init__(
            self, text, avoidParserProblems, initialTextIsEverything)

    def handle_charref(self, ref):
        t = unescape("&#%s;"%ref, self._entitydefs, self._encoding)
        self.handle_data(t)
    def handle_entityref(self, ref):
        t = unescape("&%s;"%ref, self._entitydefs, self._encoding)
        self.handle_data(t)
    def unescape_attrs(self, attrs):
        escaped_attrs = []
        for key, val in attrs:
            val = unescape(val, self._entitydefs, self._encoding)
            escaped_attrs.append((key, val))
        return escaped_attrs

class RobustLinksFactory:

    compress_re = COMPRESS_RE

    def __init__(self,
                 link_parser_class=None,
                 link_class=Link,
                 urltags=None,
                 ):
        if link_parser_class is None:
            link_parser_class = MechanizeBs
        self.link_parser_class = link_parser_class
        self.link_class = link_class
        if urltags is None:
            urltags = {
                "a": "href",
                "area": "href",
                "frame": "src",
                "iframe": "src",
                }
        self.urltags = urltags
        self._bs = None
        self._encoding = None
        self._base_url = None

    def set_soup(self, soup, base_url, encoding):
        self._bs = soup
        self._base_url = base_url
        self._encoding = encoding

    def links(self):
        bs = self._bs
        base_url = self._base_url
        encoding = self._encoding
        for ch in bs.recursiveChildGenerator():
            if (isinstance(ch, _beautifulsoup.Tag) and
                ch.name in self.urltags.keys()+["base"]):
                link = ch
                attrs = bs.unescape_attrs(link.attrs)
                attrs_dict = dict(attrs)
                if link.name == "base":
                    base_href = attrs_dict.get("href")
                    if base_href is not None:
                        base_url = base_href
                    continue
                url_attr = self.urltags[link.name]
                url = attrs_dict.get(url_attr)
                if not url:
                    continue
                url = _rfc3986.clean_url(url, encoding)
                text = link.fetchText(lambda t: True)
                if not text:
                    # follow _pullparser's weird behaviour rigidly
                    if link.name == "a":
                        text = ""
                    else:
                        text = None
                else:
                    text = self.compress_re.sub(" ", " ".join(text).strip())
                yield Link(base_url, url, text, link.name, attrs)


class RobustFormsFactory(FormsFactory):
    def __init__(self, *args, **kwds):
        args = form_parser_args(*args, **kwds)
        if args.form_parser_class is None:
            args.form_parser_class = _form.RobustFormParser
        FormsFactory.__init__(self, **args.dictionary)

    def set_response(self, response, encoding):
        self._response = response
        self.encoding = encoding


class RobustTitleFactory:
    def __init__(self):
        self._bs = self._encoding = None

    def set_soup(self, soup, encoding):
        self._bs = soup
        self._encoding = encoding

    def title(self):
        title = self._bs.first("title")
        if title == _beautifulsoup.Null:
            return None
        else:
            inner_html = "".join([str(node) for node in title.contents])
            return COMPRESS_RE.sub(" ", inner_html.strip())


class Factory:
    """Factory for forms, links, etc.

    This interface may expand in future.

    Public methods:

    set_request_class(request_class)
    set_response(response)
    forms()
    links()

    Public attributes:

    Note that accessing these attributes may raise ParseError.

    encoding: string specifying the encoding of response if it contains a text
     document (this value is left unspecified for documents that do not have
     an encoding, e.g. an image file)
    is_html: true if response contains an HTML document (XHTML may be
     regarded as HTML too)
    title: page title, or None if no title or not HTML
    global_form: form object containing all controls that are not descendants
     of any FORM element, or None if the forms_factory does not support
     supplying a global form

    """

    LAZY_ATTRS = ["encoding", "is_html", "title", "global_form"]

    def __init__(self, forms_factory, links_factory, title_factory,
                 encoding_finder=EncodingFinder(DEFAULT_ENCODING),
                 response_type_finder=ResponseTypeFinder(allow_xhtml=False),
                 ):
        """

        Pass keyword arguments only.

        default_encoding: character encoding to use if encoding cannot be
         determined (or guessed) from the response.  You should turn on
         HTTP-EQUIV handling if you want the best chance of getting this right
         without resorting to this default.  The default value of this
         parameter (currently latin-1) may change in future.

        """
        self._forms_factory = forms_factory
        self._links_factory = links_factory
        self._title_factory = title_factory
        self._encoding_finder = encoding_finder
        self._response_type_finder = response_type_finder

        self.set_response(None)

    def set_request_class(self, request_class):
        """Set request class (mechanize.Request by default).

        HTMLForm instances returned by .forms() will return instances of this
        class when .click()ed.

        """
        self._forms_factory.request_class = request_class

    def set_response(self, response):
        """Set response.

        The response must either be None or implement the same interface as
        objects returned by mechanize.urlopen().

        """
        self._response = response
        self._forms_genf = self._links_genf = None
        self._get_title = None
        for name in self.LAZY_ATTRS:
            try:
                delattr(self, name)
            except AttributeError:
                pass

    def __getattr__(self, name):
        if name not in self.LAZY_ATTRS:
            return getattr(self.__class__, name)

        if name == "encoding":
            self.encoding = self._encoding_finder.encoding(
                copy.copy(self._response))
            return self.encoding
        elif name == "is_html":
            self.is_html = self._response_type_finder.is_html(
                copy.copy(self._response), self.encoding)
            return self.is_html
        elif name == "title":
            if self.is_html:
                self.title = self._title_factory.title()
            else:
                self.title = None
            return self.title
        elif name == "global_form":
            self.forms()
            return self.global_form

    def forms(self):
        """Return iterable over HTMLForm-like objects.

        Raises mechanize.ParseError on failure.
        """
        # this implementation sets .global_form as a side-effect, for benefit
        # of __getattr__ impl
        if self._forms_genf is None:
            try:
                self._forms_genf = CachingGeneratorFunction(
                    self._forms_factory.forms())
            except:  # XXXX define exception!
                self.set_response(self._response)
                raise
            self.global_form = getattr(
                self._forms_factory, "global_form", None)
        return self._forms_genf()

    def links(self):
        """Return iterable over mechanize.Link-like objects.

        Raises mechanize.ParseError on failure.
        """
        if self._links_genf is None:
            try:
                self._links_genf = CachingGeneratorFunction(
                    self._links_factory.links())
            except:  # XXXX define exception!
                self.set_response(self._response)
                raise
        return self._links_genf()

class DefaultFactory(Factory):
    """Based on sgmllib."""
    def __init__(self, i_want_broken_xhtml_support=False):
        Factory.__init__(
            self,
            forms_factory=FormsFactory(),
            links_factory=LinksFactory(),
            title_factory=TitleFactory(),
            response_type_finder=ResponseTypeFinder(
                allow_xhtml=i_want_broken_xhtml_support),
            )

    def set_response(self, response):
        Factory.set_response(self, response)
        if response is not None:
            self._forms_factory.set_response(
                copy.copy(response), self.encoding)
            self._links_factory.set_response(
                copy.copy(response), response.geturl(), self.encoding)
            self._title_factory.set_response(
                copy.copy(response), self.encoding)

class RobustFactory(Factory):
    """Based on BeautifulSoup, hopefully a bit more robust to bad HTML than is
    DefaultFactory.

    """
    def __init__(self, i_want_broken_xhtml_support=False,
                 soup_class=None):
        Factory.__init__(
            self,
            forms_factory=RobustFormsFactory(),
            links_factory=RobustLinksFactory(),
            title_factory=RobustTitleFactory(),
            response_type_finder=ResponseTypeFinder(
                allow_xhtml=i_want_broken_xhtml_support),
            )
        if soup_class is None:
            soup_class = MechanizeBs
        self._soup_class = soup_class

    def set_response(self, response):
        Factory.set_response(self, response)
        if response is not None:
            data = response.read()
            soup = self._soup_class(self.encoding, data)
            self._forms_factory.set_response(
                copy.copy(response), self.encoding)
            self._links_factory.set_soup(
                soup, response.geturl(), self.encoding)
            self._title_factory.set_soup(soup, self.encoding)
