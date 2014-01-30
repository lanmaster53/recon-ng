import framework
# unique to module
from cookielib import CookieJar
import urllib
import re
import time
import random

class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', self.global_options.description['domain'])
        self.info = {
                     'Name': 'Bing Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from Bing.com by using the \'site\' search operator and updates the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }

    def module_run(self):
        domain = self.options['domain']
        base_url = 'http://www.bing.com/search'
        base_query = 'domain:' + domain
        pattern = '"sb_tlst"><h3><a href="(?:\w*://)*(\S+?)\.%s[^"]*"' % (domain)
        subs = []
        cnt = 0
        # control variables
        new = True
        page = 0
        nr = 50
        cookiejar = CookieJar()
        cookiejar.set_cookie(self.make_cookie('SRCHHPGUSR', 'NEWWND=0&NRSLT=%d&SRCHLANG=&AS=1' % (nr), '.bing.com'))
        # execute search engine queries and scrape results storing subdomains in a list
        # loop until no new subdomains are found
        while new == True:
            content = None
            query = ''
            # build query based on results of previous results
            for sub in subs:
                query += ' -domain:%s.%s' % (sub, domain)
            full_query = base_query + query
            url = '%s?first=%d&q=%s' % (base_url, (page*nr), urllib.quote_plus(full_query))
            # bing errors out at > 2059 characters not including the protocol
            if len(url) > 2066: url = url[:2066]
            self.verbose('URL: %s' % (url))
            # send query to search engine
            resp = self.request(url, cookiejar=cookiejar)
            if resp.status_code != 200:
                self.alert('Bing has encountered an error. Please submit an issue for debugging.')
                break
            content = resp.text
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
                    self.verbose('No New Subdomains Found on the Current Page. Jumping to Result %d.' % ((page*nr)+1))
                    new = True
            # sleep script to avoid lock-out
            self.verbose('Sleeping to avoid lockout...')
            time.sleep(random.randint(5,15))
        self.output('%d total hosts found.' % (len(subs)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
