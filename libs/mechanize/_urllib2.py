# urllib2 work-alike interface
# ...from urllib2...
from urllib2 import \
     URLError, \
     HTTPError
# ...and from mechanize
from _auth import \
     HTTPProxyPasswordMgr, \
     HTTPSClientCertMgr
from _debug import \
     HTTPResponseDebugProcessor, \
     HTTPRedirectDebugProcessor
# crap ATM
## from _gzip import \
##      HTTPGzipProcessor
from _urllib2_fork import \
     AbstractBasicAuthHandler, \
     AbstractDigestAuthHandler, \
     BaseHandler, \
     CacheFTPHandler, \
     FileHandler, \
     FTPHandler, \
     HTTPBasicAuthHandler, \
     HTTPCookieProcessor, \
     HTTPDefaultErrorHandler, \
     HTTPDigestAuthHandler, \
     HTTPErrorProcessor, \
     HTTPHandler, \
     HTTPPasswordMgr, \
     HTTPPasswordMgrWithDefaultRealm, \
     HTTPRedirectHandler, \
     ProxyBasicAuthHandler, \
     ProxyDigestAuthHandler, \
     ProxyHandler, \
     UnknownHandler
from _http import \
     HTTPEquivProcessor, \
     HTTPRefererProcessor, \
     HTTPRefreshProcessor, \
     HTTPRobotRulesProcessor, \
     RobotExclusionError
import httplib
if hasattr(httplib, 'HTTPS'):
    from _urllib2_fork import HTTPSHandler
del httplib
from _opener import OpenerDirector, \
     SeekableResponseOpener, \
     build_opener, install_opener, urlopen
from _request import \
     Request
