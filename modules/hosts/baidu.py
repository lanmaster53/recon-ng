import _cmd
import __builtin__
# unique to module
import urllib
import urllib2
import re
import time
import random

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain'],
                        'user-agent': self.goptions['user-agent'],
                        'verbose': False
                        }

    def do_info(self, params):
        print ''
        print 'Harvests hosts from Google.com by using the \'site\' search operator.'
        print ''

    def do_run(self, params):
        self.get_hosts()
    
    def get_hosts(self):#wd=site%3Asans.org+-site%3Awww.sans.org
        domain = self.options['domain']
        verbose = self.options['verbose']
        user_agent = self.options['user-agent']
        base_url = 'http://www.baidu.com'
        base_uri = '/s?'
        base_query = 'site:' + domain
        pattern = '<span class="g">\s\s(\S*?)\.%s.*?</span>'  % (domain)
        subs = []
        # control variables
        new = True
        page = 0
        nr = 10
        # execute search engine queries and scrape results storing subdomains in a list
        # loop until no new subdomains are found
        while new == True:
            content = None
            query = ''
            # build query based on results of previous results
            for sub in subs:
                query += ' -site:%s.%s' % (sub, domain)
            full_query = base_query + query
            start_param = 'pn=%d' % (page*nr)
            query_param = 'wd=%s' % (urllib.quote_plus(full_query))
            #rn=10
            #cl=3
            params = '%s&%s' % (query_param, start_param)
            full_url = base_url + base_uri + params
            # note: typical URI max length is 2048 (starts after top level domain)
            if verbose: print '[URL] %s' % full_url
            # build and send request
            request = urllib2.Request(full_url)
            request.add_header('User-Agent', user_agent)
            # send query to search engine
            try: content = self.web_req(request)
            except KeyboardInterrupt: pass
            except Exception as e: self.error('%s. Exiting.' % str(e))
            if not content: break
            content = content.read()
            #import pdb;pdb.set_trace()
            sites = re.findall(pattern, content)
            # create a unique list
            sites = list(set(sites))
            new = False
            # add subdomain to list if not already exists
            for site in sites:
               if site not in subs:
                    subs.append(site)
                    new = True
                    host = '%s.%s' % (site, domain)
                    print '[Host] %s' % (host)
                    self.add_host(host)
            # exit if maximum number of queries has been made
            # start going through all pages if query size is maxed out
            if not new:
                # exit if all subdomains have been found
                if not u'>\u4e0b\u4e00\u9875&gt;<'.encode('utf-8') in content:
                    break
                else:
                    page += 1
                    if verbose: print '[*] No New Subdomains Found on the Current Page. Jumping to Result %d.' % ((page*nr)+1)
                    new = True
            # sleep script to avoid lock-out
            if verbose: print '[*] Sleeping to Avoid Lock-out...'
            try: time.sleep(random.randint(5,15))
            except KeyboardInterrupt: break
        if verbose: print '[*] Final Query String: %s' % (full_url)