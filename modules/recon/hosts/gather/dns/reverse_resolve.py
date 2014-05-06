import module
# unique to module
import dns.resolver
import dns.reversename
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL ORDER BY netblock')
        self.register_option('nameserver', '8.8.8.8', 'yes', 'ip address of a valid nameserver')
        self.register_option('timeout', 2, 'yes', 'maximum lifetime of dns queries')
        self.register_option('attempts', 3, 'yes', 'number of retry attempts per host')
        self.info = {
                     'Name': 'Reverse Resolver',
                     'Author': 'John Babio (@3vi1john)',
                     'Description': 'Conducts a reverse lookup for each of a netblock\'s IP addresses to resolve the hostname. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, netblocks):
        # build a regex that matches any of the stored domains
        domains = [x[0] for x in self.query('SELECT DISTINCT domain from domains WHERE domain IS NOT NULL')]
        regex = '(?:%s)' % ('|'.join(['\.' + x.replace('.', r'\.') for x in domains]))
        max_attempts = self.options['attempts']
        resolver = dns.resolver.get_default_resolver()
        resolver.nameservers = [self.options['nameserver']]
        resolver.lifetime = self.options['timeout']
        cnt = 0
        new = 0
        for netblock in netblocks:
            self.heading(netblock, level=0)
            addresses = self.cidr_to_list(netblock)
            for address in addresses:
                attempt = 0
                while attempt < max_attempts:
                    try:
                        addr = dns.reversename.from_address(address)
                        hosts = resolver.query(addr,'PTR')
                    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                        self.verbose('%s => No record found.' % (address))
                    except dns.resolver.Timeout:
                        self.verbose('%s => Request timed out.' % (address))
                        attempt += 1
                        continue
                    except (dns.resolver.NoNameservers):
                        self.error('Invalid nameserver.')
                        return
                    else:
                        for host in hosts:
                            host = str(host)[:-1] # slice the trailing dot
                            if re.search(regex, host):
                                new += self.add_hosts(host, address)
                            cnt += 1
                            self.alert('%s => %s' % (address, host))
                    # break out of the loop
                    attempt = max_attempts
        self.summarize(new, cnt)
