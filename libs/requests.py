import json
import socket
import ssl
import urllib
import urllib2

# create a global ssl context that ignores certificate validation
if hasattr(ssl, '_create_unverified_context'): 
    ssl._create_default_https_context = ssl._create_unverified_context

class Request(object):

    def __init__(self, **kwargs):
        '''Initializes control parameters as class attributes.'''
        self.user_agent = "Python-urllib/%s" % (urllib2.__version__) if 'user_agent' not in kwargs else kwargs['user_agent']
        self.debug = False if 'debug' not in kwargs else kwargs['debug']
        self.proxy = None if 'proxy' not in kwargs else kwargs['proxy']
        self.timeout = None if 'timeout' not in kwargs else kwargs['timeout']
        self.redirect = True if 'redirect' not in kwargs else kwargs['redirect']

    def send(self, url, method='GET', payload=None, headers=None, cookiejar=None, auth=None, content=''):
        '''Makes a web request and returns a response object.'''
        if method.upper() != 'POST' and content:
            raise RequestException('Invalid content type for the %s method: %s' % (method, content))
        # prime local mutable variables to prevent persistence
        if payload is None: payload = {}
        if headers is None: headers = {}
        if auth is None: auth = ()

        # set request arguments
        # process user-agent header
        headers['User-Agent'] = self.user_agent
        # process payload
        if content.upper() == 'JSON':
            headers['Content-Type'] = 'application/json'
            payload = json.dumps(payload)
        else:
            payload = urllib.urlencode(payload)
        # process basic authentication
        if len(auth) == 2:
            authorization = ('%s:%s' % (auth[0], auth[1])).encode('base64').replace('\n', '')
            headers['Authorization'] = 'Basic %s' % (authorization)
        # process socket timeout
        if self.timeout:
            socket.setdefaulttimeout(self.timeout)
        
        # set handlers
        # declare handlers list according to debug setting
        handlers = [urllib2.HTTPHandler(debuglevel=1), urllib2.HTTPSHandler(debuglevel=1)] if self.debug else []
        # process cookiejar handler
        if cookiejar != None:
            handlers.append(urllib2.HTTPCookieProcessor(cookiejar))
        # process redirect and add handler
        if self.redirect == False:
            handlers.append(NoRedirectHandler)
        # process proxies and add handler
        if self.proxy:
            proxies = {'http': self.proxy, 'https': self.proxy}
            handlers.append(urllib2.ProxyHandler(proxies))

        # install opener
        opener = urllib2.build_opener(*handlers)
        urllib2.install_opener(opener)

        # process method and make request
        if method == 'GET':
            if payload: url = '%s?%s' % (url, payload)
            req = urllib2.Request(url, headers=headers)
        elif method == 'POST':
            req = urllib2.Request(url, data=payload, headers=headers)
        elif method == 'HEAD':
            if payload: url = '%s?%s' % (url, payload)
            req = urllib2.Request(url, headers=headers)
            req.get_method = lambda : 'HEAD'
        else:
            raise RequestException('Request method \'%s\' is not a supported method.' % (method))
        try:
            resp = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            resp = e

        # build and return response object
        return ResponseObject(resp, cookiejar)

class NoRedirectHandler(urllib2.HTTPRedirectHandler):

    def http_error_302(self, req, fp, code, msg, headers):
        pass

    http_error_301 = http_error_303 = http_error_307 = http_error_302

import xml.etree.ElementTree
import StringIO

class ResponseObject(object):

    def __init__(self, resp, cookiejar):
        # set raw response property
        self.raw = resp.read()
        # set inherited properties
        self.url = resp.geturl()
        self.status_code = resp.getcode()
        self.headers = resp.headers.dict
        # detect and set encoding property
        self.encoding = resp.headers.getparam('charset')
        self.content_type = resp.headers.getheader('content-type')
        self.cookiejar = cookiejar

    @property
    def text(self):
        try:
            return self.raw.decode(self.encoding)
        except (UnicodeDecodeError, TypeError):
            return ''.join([char for char in self.raw if ord(char) in [9,10,13] + range(32, 126)])

    @property
    def json(self):
        try:
            return json.loads(self.text)
        except ValueError:
            return None

    @property
    def xml(self):
        try:
            return xml.etree.ElementTree.parse(StringIO.StringIO(self.text))
        except xml.etree.ElementTree.ParseError:
            return None

class RequestException(Exception):
    pass
