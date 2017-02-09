from recon.core.module import BaseModule
from urlparse import urlparse

class Module(BaseModule):

    meta = {
        'name': 'Google CSE Hostname Enumerator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages the Google Custom Search Engine API to harvest hosts using the \'site\' search operator. Updates the \'hosts\' table with the results.',
        'required_keys': ['google_api', 'google_cse'],
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        for domain in domains:
            self.heading(domain, level=0)
            base_query = 'site:' + domain
            hosts = []
            while True:
                query = ''
                # build query based on results of previous results
                for host in hosts:
                    query += ' -site:%s' % (host)
                query = base_query + query
                results = self.search_google_api(query, limit=1)
                if not results: break
                for result in results:
                    host = urlparse(result['link']).netloc
                    if not host in hosts:
                        hosts.append(host)
                        # add each host to the database
                        self.add_hosts(host)
