import framework
# unique to module
from urlparse import urlparse
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.register_option('regex', '%s$' % (self.global_options['domain']), 'no', 'regex to match for adding results to the database')
        self.info = {
                     'Name': 'Bing IP Neighbor Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the Bing API and "ip:" advanced search operator to enumerate other virtual hosts sharing the same IP address.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        addresses = self.get_source(self.options['source'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        regex = self.options['regex']

        new = 0
        hosts = []
        for address in addresses:
            query = '\'ip:%s\'' % (address)
            results = self.search_bing_api(query)
            if type(results) != list: break
            if not results: self.verbose('No additional hosts discovered at \'%s\'.' % (address))
            for result in results:
                host = urlparse(result['Url']).netloc
                if not host in hosts:
                    hosts.append(host)
                    self.output(host)
                    # add each host to the database
                    if not regex or re.search(regex, host):
                        new += self.add_host(host, address)

        self.output('%d total hosts found.' % (len(hosts)))
        if new: self.alert('%d NEW hosts found!' % (new))
