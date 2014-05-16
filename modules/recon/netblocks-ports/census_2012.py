import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL ORDER BY netblock')
        self.info = {
                     'Name': 'Internet Census 2012 Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the Internet Census 2012 data through Exfiltrated.com to enumerate open ports for a netblock.',
                     'Comments': [
                                  'http://exfiltrated.com/querystart.php'
                                  ]
                     }

    def module_run(self, netblocks):
        url = 'http://exfiltrated.com/query.php'
        cnt = 0
        new = 0
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
                self.output('%s (%s) - %s' % (address, hostname, port))
                new += self.add_ports(ip_address=address, host=hostname, port=port)
                cnt += 1
            if not hosts:
                self.output('No scan data available.')
        self.summarize(new, cnt)
