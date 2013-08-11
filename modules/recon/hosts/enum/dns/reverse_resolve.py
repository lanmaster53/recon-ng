import framework
# unique to module
import dns.resolver
import dns.reversename





class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('subnet', '8.8.8', 'yes', 'First the octests of the subnet')
        self.info = {
                     'Name': 'Reverse Resolver',
                     'Author': 'John Babio (@3vi1john)',
                     'Description': 'Does a reverse lookup of IP address to hostname for the given subnet.',
                     'Comments': [
                                  'Note: Subnet must be the first 3 octets without a period. Example 192.168.1 ']
                     }

    def module_run(self):
        node = 1
        subnet = self.options['subnet']['value']
        
        while node <= 254: 
            ip = subnet + '.' + str(node)
        
            try:
                addr = dns.reversename.from_address(ip)
                hostname = str(dns.resolver.query(addr,"PTR")[0])
                self.output("IP Address %s has hostname %s\n" % (ip, hostname))
                self.add_host(hostname,ip_address=ip)
                node = node +1
                    
            except  dns.resolver.NXDOMAIN:
                    self.output("%s: NXDOMAIN\n"%(ip))
                    node = node +1