from framework import *
# unique to module
from urlparse import urlparse

class Module(Framework):

    def __init__(self, params):
        Framework.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', self.global_options.description['domain'])
        self.info = {
                     'Name': 'Google CSE Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the Google Custom Search Engine API to harvest hosts using the \'site\' search operator and updates the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }

    def module_run(self):
        domain = self.options['domain']

        base_query = 'site:' + domain
        hosts = []
        new = 0
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
                    new += self.add_host(host)

        self.output('%d total hosts found.' % (len(hosts)))
        if new: self.alert('%d NEW hosts found!' % (new))
