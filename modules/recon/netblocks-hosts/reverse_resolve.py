import module
# unique to module
import dns.resolver
import dns.reversename

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL')
        self.info = {
                     'Name': 'Reverse Resolver',
                     'Author': 'John Babio (@3vi1john)',
                     'Description': 'Conducts a reverse lookup for each of a netblock\'s IP addresses to resolve the hostname. Updates the \'hosts\' table with the results.'
                     }

    def module_run(self, netblocks):
        max_attempts = 3
        resolver = self.get_resolver()
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
                            new += self.add_hosts(host, address)
                            cnt += 1
                            self.alert('%s => %s' % (address, host))
                    # break out of the loop
                    attempt = max_attempts
        self.summarize(new, cnt)
