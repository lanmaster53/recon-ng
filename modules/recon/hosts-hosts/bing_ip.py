from recon.core.module import BaseModule
from recon.utils.parsers import parse_hostname
from urlparse import urlparse
import re

class Module(BaseModule):

    meta = {
        'name': 'Bing API IP Neighbor Enumerator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages the Bing API and "ip:" advanced search operator to enumerate other virtual hosts sharing the same IP address. Updates the \'hosts\' table with the results.',
        'required_keys': ['bing_api'],
        'comments': (
            'This module only stores hosts whose domain matches an entry in the domains table.',
        ),
        'query': 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL',
        'options': (
            ('restrict', True, True, 'restrict added hosts to current domains'),
        ),
    }

    def module_run(self, addresses):
        # build a regex that matches any of the stored domains
        domains = [x[0] for x in self.query('SELECT DISTINCT domain from domains WHERE domain IS NOT NULL')]
        regex = '(?:%s)' % ('|'.join(['\.'+re.escape(x)+'$' for x in domains]))
        for address in addresses:
            self.heading(address, level=0)
            query = 'ip:%s' % (address)
            results = self.search_bing_api(query)
            if not results:
                self.verbose('No additional hosts discovered at \'%s\'.' % (address))
            for result in results:
                host = parse_hostname(result['displayUrl'])
                self.verbose(host)
                # apply restriction
                if self.options['restrict'] and not re.search(regex, host):
                    continue
                # add hosts to the database
                self.add_hosts(host, address)
