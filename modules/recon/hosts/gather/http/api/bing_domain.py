import module
# unique to module
from urlparse import urlparse
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', self.global_options.description['domain'])
        self.register_option('limit', 0, 'yes', 'limit number of api requests (0 = unlimited)')
        self.info = {
                     'Name': 'Bing API Hostname Enumerator',
                     'Author': 'Marcus Watson (@BranMacMuffin)',
                     'Description': 'Leverages the Bing API and "domain:" advanced search operator to harvest hosts and update the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Note: \'LIMIT\' option limits the number of API requests in order to prevent API query exhaustion.'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']
        limit = self.options['limit']
        hosts = []
        results = []
        pages = 1
        requests = 0
        cnt = 0
        base_query = '\'domain:%s' % (domain)

        while not limit or requests < limit:

            query = base_query

            # build query string based on api limitations
            for host in hosts:
                omit_domain = ' -domain:%s' % (host)
                if len(query) + len(omit_domain) < 1425:
                    query += omit_domain
                else:
                    break
            query += '\''

            # make api requests
            if limit and requests + pages > limit:
                pages = limit - requests
            last_len = len(results)
            results = self.search_bing_api(query, pages)
            requests += pages

            # iterate through results and add new hosts
            new = False
            for result in results:
                host = urlparse(result['Url']).netloc
                if not host in hosts and host != domain:
                    hosts.append(host)
                    self.output(host)
                    cnt += self.add_host(host)
                    new = True

            if not new and last_len == len(results):
                break
            elif not new and last_len != len(results):
                pages += 1
                self.verbose('No new hosts found for the current query. Increasing depth to \'%d\' pages.' % (pages))

        self.verbose('%d total API requests made.' % (requests))
        self.output('%d total hosts found.' % (len(hosts)))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
