from recon.core.module import BaseModule
from urlparse import urlparse
import re

class Module(BaseModule):

    meta = {
        'name': 'Bing API Hostname Enumerator',
        'author': 'Marcus Watson (@BranMacMuffin)',
        'description': 'Leverages the Bing API and "domain:" advanced search operator to harvest hosts. Updates the \'hosts\' table with the results.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
        'options': (
            ('limit', 0, True, 'limit total number of api requests (0 = unlimited)'),
        ),
    }

    def module_run(self, domains):
        limit = self.options['limit']
        requests = 0
        for domain in domains:
            self.heading(domain, level=0)
            hosts = []
            results = []
            pages = 1
            base_query = 'domain:%s' % (domain)
            while not limit or requests < limit:
                query = base_query
                # build query string based on api limitations
                for host in hosts:
                    omit_domain = ' -domain:%s' % (host)
                    if len(query) + len(omit_domain) < 1425:
                        query += omit_domain
                    else:
                        break
                # make api requests
                if limit and requests + pages > limit:
                    pages = limit - requests
                last_len = len(results)
                results = self.search_bing_api(query, pages)
                requests += pages
                # iterate through results and add new hosts
                flag = False
                for result in results:
                    host = urlparse(result['Url']).netloc
                    if host.endswith('.'+domain) and host not in hosts:
                        hosts.append(host)
                        self.output(host)
                        self.add_hosts(host)
                        flag = True
                if not flag and last_len == len(results):
                    break
                elif not flag and last_len != len(results):
                    pages += 1
                    self.verbose('No new hosts found for the current query. Increasing depth to \'%d\' pages.' % (pages))
