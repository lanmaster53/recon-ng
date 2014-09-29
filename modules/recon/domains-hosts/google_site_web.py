import module
# unique to module
import urllib
import re
import time
import random

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
                     'Name': 'Google Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from Google.com by using the \'site\' search operator. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, domains):
        base_url = 'https://www.google.com/search'
        cnt = 0
        new = 0
        for domain in domains:
            self.heading(domain, level=0)
            base_query = 'site:' + domain
            pattern = '<cite>(?:\w*://)*(\S*?)\.%s[^<]*</cite>'  % (domain)
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
                url = '%s?start=%d&filter=0&q=%s' % (base_url, (page*nr), urllib.quote_plus(full_query))
                # google errors out at > 2061 characters not including the protocol
                if len(url) > 2068: url = url[:2068]
                self.verbose('URL: %s' % (url))
                # send query to search engine
                resp = self.request(url, redirect=False)
                if resp.status_code != 200:
                    if resp.status_code == 302:
                        self.alert('You\'ve been temporarily banned by Google for violating the terms of service.')
                    else:
                        self.alert('Google has encountered an error. Please submit an issue for debugging.')
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
                        new += self.add_hosts(host)
                if not new:
                    # exit if all subdomains have been found
                    if not '>Next</span>' in content:
                        break
                    else:
                        page += 1
                        self.verbose('No New Subdomains Found on the Current Page. Jumping to Result %d.' % ((page*nr)+1))
                        new = True
                # sleep script to avoid lock-out
                self.verbose('Sleeping to avoid lockout...')
                time.sleep(random.randint(5,15))
            cnt += len(subs)
        self.summarize(new, cnt)
