from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Shodan Network Enumerator',
        'author': 'Mike Siegel and Tim Tomes (@LaNMaSteR53)',
        'description': 'Harvests hosts from the Shodan API by using the \'net\' search operator. Updates the \'hosts\' table with the results.',
        'required_keys': ['shodan_api'],
        'query': 'SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL',
        'options': (
            ('limit', 1, True, 'limit number of api requests per input source (0 = unlimited)'),
        ),
    }

    def module_run(self, netblocks):
        limit = self.options['limit']
        for netblock in netblocks:
            self.heading(netblock, level=0)
            query = 'net:%s' % (netblock)
            results = self.search_shodan_api(query, limit)
            for host in results:
                address = host['ip_str']
                port = host['port']
                if not host['hostnames']:
                    host['hostnames'] = [None]
                for hostname in host['hostnames']:
                    self.add_ports(ip_address=address, port=port, host=hostname)
                    self.add_hosts(host=hostname, ip_address=address)
