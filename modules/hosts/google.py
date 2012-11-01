import _cmd
import __builtin__
# unique to module
import urllib
import urllib2
import sys
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
                     'Name': 'Google Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from Google.com by using the \'site\' search operator.',
                     'Comments': []
                     }

    def do_run(self, params):
        self.get_hosts()
    
    def get_hosts(self):
        domain = self.options['domain']
        verbose = self.goptions['verbose']
        base_url = 'http://www.google.com'
        base_uri = '/search?'
        base_query = 'site:' + domain
        pattern = '<a\shref="\w+://(\S+?)\.%s\S+?"\sclass=l'  % (domain)
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
            start_param = 'start=%d' % (page*nr)
            query_param = 'q=%s' % (urllib.quote_plus(full_query))
            if len(base_uri) + len(query_param) + 1 + len(start_param) < 2048:
                last_query_param = query_param
                params = '%s&%s' % (query_param, start_param)
            else:
                params = last_query_param[:2047-len(start_param)-len(base_uri)] + start_param
            full_url = base_url + base_uri + params
            # note: query character limit is passive in mobile, but seems to be ~794
            # note: query character limit seems to be 852 for desktop queries
            # note: typical URI max length is 2048 (starts after top level domain)
            if verbose: self.output('URL: %s' % full_url)
            # build and send request
            request = urllib2.Request(full_url)
            # send query to search engine
            try: content = self.urlopen(request)
            except KeyboardInterrupt:
                sys.stdout.write('\n')
                pass
            except Exception as e: self.error('%s.' % (str(e)))
            if not content: return
            content = content.read()
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
                    self.output('%s' % (host))
                    self.add_host(host)
            # exit if maximum number of queries has been made
            # start going through all pages if query size is maxed out
            if not new:
                # exit if all subdomains have been found
                if not '>Next</span>' in content:
                    break
                else:
                    page += 1
                    if verbose: self.output('No New Subdomains Found on the Current Page. Jumping to Result %d.' % ((page*nr)+1))
                    new = True
            # sleep script to avoid lock-out
            if verbose: self.output('Sleeping to Avoid Lock-out...')
            try: time.sleep(random.randint(5,15))
            except KeyboardInterrupt:
                sys.stdout.write('\n')
                break
        if verbose: self.output('Final Query String: %s' % (full_url))