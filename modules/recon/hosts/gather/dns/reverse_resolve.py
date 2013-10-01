import framework
# unique to module
import dns.resolver
import dns.reversename

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('subnet', None, 'yes', 'CIDR block of the target network (X.X.X.X/Y)')
        self.register_option('domain', self.goptions['domain']['value'], 'yes', 'domain to match for adding results to the database')
        self.info = {
                     'Name': 'Reverse Resolver',
                     'Author': 'John Babio (@3vi1john)',
                     'Description': 'Does a reverse lookup of IP address to hostname for the given subnet.',
                     'Comments': []
                     }

    def module_run(self):
        addresses = self.cidr_to_list(self.options['subnet']['value'])
        domain = self.options['domain']['value']

        cnt = 0
        new = 0
        for address in addresses:
            try:
                addr = dns.reversename.from_address(address)
                host = str(dns.resolver.query(addr,'PTR')[0])
                host = host[:-1] # slice trailing dot
                if host.lower().endswith(domain.lower()):
                    new += self.add_host(host, address)
                cnt += 1
                self.alert('%s => %s' % (host, address))
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                self.verbose('%s => No record found.' % (address))

        self.output('%d cntal hosts found.' % (cnt))
        if new: self.alert('%d NEW hosts found!' % (new))
