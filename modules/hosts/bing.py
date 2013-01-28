import framework
# unique to module
import urllib
import re
import time
import random

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Bing Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from Bing.com by using the \'site\' search operator. This module updates the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.get_hosts()
    
    def get_hosts(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']
        url = 'http://www.bing.com/search'
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
            payload = {'first': str(page*nr), 'q': full_query}
            #
            #
            cookies = {'SRCHHPGUSR': 'NEWWND=0&NRSLT=%d&SRCHLANG=&AS=1' % (nr)}
            if verbose: self.output('URL: %s?%s' % (url, urllib.urlencode(payload)))
            # send query to search engine
            try: content = self.request(url, payload=payload, cookies=cookies)
            except KeyboardInterrupt:
                print ''
            except Exception as e:
                self.error(e.__str__())
            if not content: break
            content = content.text
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
                    cnt += self.add_host(host)
            if not new:
                # exit if all subdomains have been found
                if not '>Next</a>' in content:
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
        if verbose: self.output('Final Query String: %s?%s' % (url, urllib.urlencode(payload)))
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))