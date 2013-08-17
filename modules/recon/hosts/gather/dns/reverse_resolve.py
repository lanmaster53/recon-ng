import framework
# unique to module
import dns.resolver
import dns.reversename





class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('subnet', '8.8.8', 'yes', 'First three octets of the subnet')
        self.info = {
                     'Name': 'Reverse Resolver',
                     'Author': 'John Babio (@3vi1john)',
                     'Description': 'Does a reverse lookup of IP address to hostname for the given subnet.',
                     'Comments': [
                                  'Note: Subnet must be the first 3 octets without a period. Example 192.168.1 ']
                     }

    def module_run(self):
        node = 1
        tot = 0
        cnt = 0
        subnet = self.options['subnet']['value']
        
        while node < 255: 
            address = '%s.%d' % (subnet, node)        
            try:
                addr = dns.reversename.from_address(address)
                host = str(dns.resolver.query(addr,'PTR')[0])
                cnt += self.add_host(host, address)
                tot += 1
                self.alert('%s => %s' % (host, address))
            except  dns.resolver.NXDOMAIN:
                self.verbose('%s => Unknown' % (address))
            node += 1

        self.output('%d total hosts found.' % (tot))
        if cnt: self.alert('%d NEW hosts found!' % (cnt))
