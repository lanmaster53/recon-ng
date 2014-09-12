import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.register_option('limit', 1, True, 'limit number of api requests per input source (0 = unlimited)')
        self.info = {
                     'Name': 'Shodan Hostname Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests hosts from the Shodanhq.com API by using the \'hostname\' search operator. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, domains):
        limit = self.options['limit']
        cnt = 0
        new = 0
        for domain in domains:
            self.heading(domain, level=0)
            query = 'hostname:%s' % (domain)
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
