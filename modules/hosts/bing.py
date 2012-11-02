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
                        'domain': self.goptions['domain']
                        }
        self.info = {
                     'Name': 'Bing Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from Bing.com by using the \'site\' search operator.',
                     'Comments': []
                     }

    def do_run(self, params):
        self.get_hosts()
    
    def get_hosts(self):
        domain = self.options['domain']
        verbose = self.goptions['verbose']
        base_url = 'http://www.bing.com'
        base_uri = '/search?'
        base_query = 'site:' + domain
        pattern = '"sb_tlst"><h3><a href="\w+://(\S+?)\.%s' % (domain)
        subs = []
        cnt = 0
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
            if verbose: self.output('URL: %s' % full_url)
            # build and send request
            request = urllib2.Request(full_url)
            request.add_header('Cookie', 'SRCHHPGUSR=NEWWND=0&NRSLT=%d&SRCHLANG=&AS=1;' % (nr))
            # send query to search engine
            try: content = self.urlopen(request)
            except KeyboardInterrupt:
                print ''
                pass
            except Exception as e: self.error('%s.' % (str(e)))
            if not content: return
            content = content.read()
            sites = re.findall(pattern, content)
            # create a uniq list
            sites = list(set(sites))
            new = False
            # add subdomain to list if not already exists
            for site in sites:
                if site not in subs:
                    subs.append(site)
                    new = True
                    host = '%s.%s' % (site, domain)
                    self.output('%s' % (host))
                    cnt += self.add_host(host)
            # exit if maximum number of queries has been made
            # start going through all pages if query size is maxed out
            if not new:
                # exit if all subdomains have been found
                if not '>Next</a>' in content:
                    # curl to stdin breaks pdb
                    break
                else:
                    page += 1
                    if verbose: self.output('No New Subdomains Found on the Current Page. Jumping to Result %d.' % ((page*nr)+1))
                    new = True
            # sleep script to avoid lock-out
            if verbose: self.output('Sleeping to Avoid Lock-out...')
            try: time.sleep(random.randint(5,15))
            except KeyboardInterrupt:
                print ''
                break
        if verbose: self.output('Final Query String: %s' % (full_url))
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))