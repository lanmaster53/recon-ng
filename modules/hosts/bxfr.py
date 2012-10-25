import _cmd
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
                        'domain': '',
                        'verbose': False,
                        'user_agent': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)'
                        }

    def do_info(self, params):
        print 'BXFR module information.'

    def do_run(self, params):
        domain = self.options['domain']
        verbose = self.options['verbose']
        user_agent = self.options['user_agent']
        base_url = 'http://www.bing.com'
        base_uri = '/search?'
        base_query = 'site:' + domain
        pattern = '"sb_tlst"><h3><a href="\w+://(\S+?)\.%s' % (domain)
        subs = []
        # control variables
        new = True
        page = 0
        nr = 50
        # execute search engine queries and scrape results storing subdomains in a list
        # loop until no new subdomains are found
        while new == True:
            content = None
            query = ''
            # build query based on results of previous results
            for sub in subs:
                query += ' -site:%s.%s' % (sub, domain)
            full_query = base_query + query
            start_param = 'first=%s' % (str(page*nr))
            query_param = 'q=%s' % (urllib.quote_plus(full_query))
            params = '%s&%s' % (query_param, start_param)
            full_url = base_url + base_uri + params
            # note: typical URI max length is 2048 (starts after top level domain)
            if verbose: print '[URL] %s' % full_url
            # build and send request
            request = urllib2.Request(full_url)
            request.add_header('User-Agent', user_agent)
            request.add_header('Cookie', 'SRCHHPGUSR=NEWWND=0&NRSLT=%d&SRCHLANG=&AS=1;' % (nr))
            requestor = urllib2.build_opener()
            # send query to search engine
            try: content = requestor.open(request)
            except KeyboardInterrupt: pass
            except Exception as e: print '[!] %s. Returning Previously Harvested Results.' % str(e)
            if not content: break
            content = content.read()
            sites = re.findall(pattern, content)
            # create a uniq list
            sites = list(set(sites))
            new = False
            # add subdomain to list if not already exists
            for site in sites:
                if site not in subs:
                    print '[Host] %s.%s' % (site, domain)
                    subs.append(site)
                    new = True
            # exit if maximum number of queries has been made
            # start going through all pages if query size is maxed out
            if not new:
                # exit if all subdomains have been found
                if not '>Next</a>' in content:
                    # curl to stdin breaks pdb
                    break
                else:
                    page += 1
                    if verbose: print '[-] No New Subdomains Found on the Current Page. Jumping to Result %d.' % ((page*nr)+1)
                    new = True
            # sleep script to avoid lock-out
            if verbose: print '[-] Sleeping to Avoid Lock-out...'
            try: time.sleep(random.randint(5,15))
            except KeyboardInterrupt: break
        # print list of subdomains
        if verbose: print '[-] Final Query String: %s' % (full_url)