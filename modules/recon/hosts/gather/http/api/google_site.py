import module
# unique to module
from urlparse import urlparse

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
                     'Name': 'Google CSE Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the Google Custom Search Engine API to harvest hosts using the \'site\' search operator. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, domains):
        cnt = 0
        new = 0
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
                        self.output(host)
                        # add each host to the database
                        new += self.add_hosts(host)
            cnt += len(hosts)
        self.summarize(new, cnt)
