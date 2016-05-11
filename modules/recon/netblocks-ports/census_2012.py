from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Internet Census 2012 Lookup',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Queries the Internet Census 2012 data through Exfiltrated.com to enumerate open ports for a netblock.',
        'comments': (
            'http://exfiltrated.com/querystart.php',
        ),
        'query': 'SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL',
    }

    def module_run(self, netblocks):
        url = 'http://exfiltrated.com/query.php'
        for netblock in netblocks:
            self.heading(netblock, level=0)
            addresses = self.cidr_to_list(netblock)
            first = addresses[0]
            last = addresses[-1]
            self.verbose('%s (%s - %s)' % (netblock, first, last))
            payload = {'startIP': first, 'endIP': last, 'includeHostnames': 'Yes', 'rawDownload': 'Yes'}
            resp = self.request(url, payload=payload)
            hosts = resp.text.strip().split('\r\n')[1:]
            for host in hosts:
                elements = host.split('\t')
                address = elements[1]
                port = elements[2]
                hostname = elements[0]
                self.add_ports(ip_address=address, host=hostname, port=port)
            if not hosts:
                self.output('No scan data available.')
