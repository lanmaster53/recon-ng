import module
# unique to module
from urlparse import urlparse
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL ORDER BY ip_address')
        self.info = {
                     'Name': 'Bing API IP Neighbor Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the Bing API and "ip:" advanced search operator to enumerate other virtual hosts sharing the same IP address. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, addresses):
        # build a regex that matches any of the stored domains
        domains = [x[0] for x in self.query('SELECT DISTINCT domain from domains WHERE domain IS NOT NULL')]
        regex = '(?:%s)' % ('|'.join(['\.' + x.replace('.', r'\.') for x in domains]))
        new = 0
        hosts = []
        for address in addresses:
            self.heading(address, level=0)
            query = '\'ip:%s\'' % (address)
            results = self.search_bing_api(query)
            if not results: self.verbose('No additional hosts discovered at \'%s\'.' % (address))
            for result in results:
                host = urlparse(result['Url']).netloc
                if not host in hosts:
                    hosts.append(host)
                    self.output(host)
                    # add each host to the database
                    if re.search(regex, host):
                        new += self.add_hosts(host, address)
        self.summarize(new, len(hosts))
