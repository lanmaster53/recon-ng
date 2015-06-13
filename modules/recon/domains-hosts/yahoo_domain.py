from recon.core.module import BaseModule
from recon.utils.requests import encode_payload
from lxml.html import fromstring
from urlparse import urlparse
import time
import random
import urllib

class Module(BaseModule):

    meta = {
        'name': 'Yahoo Hostname Enumerator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Harvests hosts from Yahoo.com by using the \'domain\' search operator. Updates the \'hosts\' table with the results.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain',
    }

    def module_run(self, domains):
        base_url = 'https://search.yahoo.com/search'
        for domain in domains:
            self.heading(domain, level=0)
            base_query = 'domain:' + domain
            hosts = []
            # control variables
            new = True
            page = 0
            nr = 100
            # execute search engine queries and scrape results storing hostnames in a list
            # loop until no new hostnames are found
            while new == True:
                content = None
                query = ''
                # build query based on results of previous results
                for host in hosts:
                    query += ' -domain:%s' % (host,)
                full_query = base_query + query
                payload = {'pz':nr, 'b':(page*nr)+1, 'p':full_query}
                # yahoo does not appear to have a max url length
                self.verbose('URL: %s?%s' % (base_url, encode_payload(payload)))
                # send query to search engine
                resp = self.request(base_url, method='POST', payload=payload)
                if resp.status_code != 200:
                    self.alert('Yahoo has encountered an error. Please submit an issue for debugging.')
                    break
                tree = fromstring(resp.text)
                sites = tree.xpath('//a[@class=" ac-algo ac-21th"]/@href')
                sites = [urlparse(x).hostname for x in sites]
                # create a unique list
                sites = list(set(sites))
                new = False
                # add hostname to list if not already exists
                for site in sites:
                    if site not in hosts:
                        hosts.append(site)
                        new = True
                        self.output(site)
                        self.add_hosts(site)
                if not new:
                    # exit if all hostnames have been found
                    if '>Next<' not in resp.text:
                        break
                    else:
                        page += 1
                        self.verbose('No New Subdomains Found on the Current Page. Jumping to Result %d.' % ((page*nr)+1))
                        new = True
                # sleep script to avoid lock-out
                self.verbose('Sleeping to avoid lockout...')
                time.sleep(random.randint(5,15))
