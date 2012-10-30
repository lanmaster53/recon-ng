import _cmd
import __builtin__
# unique to module
import urllib2
import json

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain'],
                        'restrict': False
                        }

    def do_info(self, params):
        print ''
        print 'Harvests hosts from the Shodanhq.com API by using the \'hostname\' search operator.'
        print ''
        print 'Note: \'restrict\' option limits API requests to 1 in order to prevent API query exhaustion.'
        print ''

    def do_run(self, params):
        self.get_hosts()
    
    def get_hosts(self):
        domain = self.options['domain']
        user_agent = self.goptions['user-agent']
        subs = []
        key = self.manage_key('shodan')
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
            content = None
            # uses API, so don't need to proxy
            #try: content = urllib2.urlopen(request)
            try: content = self.urlopen(request)
            except KeyboardInterrupt: pass
            except Exception as e: self.error('%s. Exiting.' % (str(e)))
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
            if self.options['restrict']: break
            if not new: break
            page += 1
            url = '%s?%s&page=%s' % (base_url, params, str(page))