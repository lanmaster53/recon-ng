import framework
# unique to module
import dns.resolver
import dns.reversename

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('subnet', None, 'yes', 'CIDR block of the target network (X.X.X.X/Y)')
        self.info = {
                     'Name': 'Reverse Resolver',
                     'Author': 'John Babio (@3vi1john)',
                     'Description': 'Does a reverse lookup of IP address to hostname for the given subnet.',
                     'Comments': []
                     }

    def module_run(self):
        addresses = self.cidr_to_list(self.options['subnet']['value'])
        tot = 0
        cnt = 0
        
        for address in addresses:
            try:
                addr = dns.reversename.from_address(address)
                host = str(dns.resolver.query(addr,'PTR')[0])
                cnt += self.add_host(host, address)
                tot += 1
                self.alert('%s => %s' % (host, address))
            except  dns.resolver.NXDOMAIN:
                self.verbose('%s => No record found.' % (address))

        self.output('%d total hosts found.' % (tot))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
