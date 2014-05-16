import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL ORDER BY netblock')
        self.register_option('limit', 1, 'yes', 'limit number of api requests per input source (0 = unlimited)')
        self.info = {
                     'Name': 'Shodan Network Enumerator',
                     'Author': 'Mike Siegel and Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from the Shodanhq.com API by using the \'net\' search operator. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, netblocks):
        limit = self.options['limit']
        cnt = 0
        new = 0
        for netblock in netblocks:
            self.heading(netblock, level=0)
            query = 'net:%s' % (netblock)
            results = self.search_shodan_api(query, limit)
            for host in results:
                address = host['ip_str']
                port = host['port']
                if not 'hostnames' in host.keys():
                    host['hostnames'] = [None]
                for hostname in host['hostnames']:
                    self.output('%s (%s) - %s' % (address, hostname, port))
                    self.add_ports(ip_address=address, port=port, host=hostname)
                    new += self.add_hosts(host=hostname, ip_address=address)
                    cnt += 1
        self.summarize(new, cnt)
