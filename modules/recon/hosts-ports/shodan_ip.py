from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Shodan IP Enumerator',
        'author': 'Tim Tomes (@LaNMaSteR53) and Matt Puckett (@t3lc0)',
        'description': 'Harvests port information from the Shodan API by using the \'ip\' search operator. Updates the \'ports\' table with the results.',
        'required_keys': ['shodan_api'],
        'query': 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL',
        'options': (
            ('limit', 1, True, 'limit number of api requests per input source (0 = unlimited)'),
        ),
    }

    def module_run(self, ipaddrs):
        limit = self.options['limit']
        for ipaddr in ipaddrs:
            self.heading(ipaddr, level=0)
            query = 'ip:%s' % (ipaddr)
            results = self.search_shodan_api(query, limit)
            for host in results:
                address = host['ip_str']
                port = host['port']
                if not host['hostnames']:
                    host['hostnames'] = [None]
                for hostname in host['hostnames']:
                    self.add_ports(ip_address=address, port=port, host=hostname)
