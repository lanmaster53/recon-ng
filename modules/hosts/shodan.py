import _cmd
import __builtin__
# unique to module
import urllib2
import json

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'domain': __builtin__.domain,
                        'verbose': False,
                        'user_agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)'
                        }

    def do_info(self, params):
        print ''
        print 'Harvests hosts from the Shodanhq.com API by using the \'hostname\' search operator.'
        print ''

    def do_run(self, params):
        self.get_hosts()
    
    def get_hosts(self):
        domain = self.options['domain']
        verbose = self.options['verbose']
        user_agent = self.options['user_agent']
        subs = []
        key = self.get_key('shodan')
        if not key:
            self.default('No API Key.')
            return
        base_url = 'http://www.shodanhq.com/api/search'
        params = 'q=hostname:%s&key=%s' % (domain, key)
        url = '%s?%s' % (base_url, params)
        page = 1
        # loop until no results are returned
        while True:
            new = False
            # build and send request
            request = urllib2.Request(url)
            request.add_header('User-Agent', user_agent)
            #handler = urllib2.HTTPHandler(debuglevel=1)
            requestor = urllib2.build_opener()
            content = None
            try: content = requestor.open(request)
            except KeyboardInterrupt: pass
            except Exception as e:
                print '[!] Error: %s.' % (str(e))
            if not content: break
            content = content.read()
            jsonobj = json.loads(content)
            try: results = jsonobj['matches']
            except KeyError: break
            for result in results:
                hostnames = result['hostnames']
                for hostname in hostnames:
                    site = '.'.join(hostname.split('.')[:-2])
                    if site and site not in subs:
                        subs.append(site)
                        new = True
                        host = '%s.%s' % (site, domain)
                        print '[Host] %s' % (host)
                        self.add_host(host)
            #break # large results will exhaust API query pool. Use this to restrict to one page.
            if not new: break
            page += 1
            url = '%s?%s&page=%s' % (base_url, params, str(page))