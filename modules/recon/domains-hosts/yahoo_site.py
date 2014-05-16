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
                     'Name': 'Yahoo Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from Yahoo.com by using the \'site\' search operator. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, domains):
        base_url = 'http://search.yahoo.com/search'
        cnt = 0
        new = 0
        for domain in domains:
            self.heading(domain, level=0)
            base_query = 'site:' + domain
            pattern = 'url>(?:<b>)*(?:\w*://)*(\S+?)\.(?:<b>)*%s[^<]*</b>' % (domain)
            subs = []
            # control variables
            new = True
            page = 0
            nr = 100
            # execute search engine queries and scrape results storing subdomains in a list
            # loop until no new subdomains are found
            while new == True:
                content = None
                query = ''
                # build query based on results of previous results
                for sub in subs:
                    query += ' -site:%s.%s' % (sub, domain)
                full_query = base_query + query
                url = '%s?n=%d&b=%d&p=%s' % (base_url, nr, (page*nr), urllib.quote_plus(full_query))
                # yahoo does not appear to have a max url length
                self.verbose('URL: %s' % (url))
                # send query to search engine
                resp = self.request(url)
                if resp.status_code != 200:
                    self.alert('Yahoo has encountered an error. Please submit an issue for debugging.')
                    break
                content = resp.text
                sites = re.findall(pattern, content)
                # create a unique list
                sites = list(set(sites))
                new = False
                # add subdomain to list if not already exists
                for site in sites:
                    # remove left over bold tags remaining after regex
                    site = site.replace('<b>', '')
                    site = site.replace('</b>', '')
                    if site not in subs:
                        subs.append(site)
                        new = True
                        host = '%s.%s' % (site, domain)
                        self.output('%s' % (host))
                        new += self.add_hosts(host)
                if not new:
                    # exit if all subdomains have been found
                    if not 'Next &gt;</a>' in content:
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
