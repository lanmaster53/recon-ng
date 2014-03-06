import module
# unique to module
import dns.resolver
import dns.reversename
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('netblock', self.global_options['netblock'], 'yes', self.global_options.description['netblock'])
        self.register_option('regex', '%s$' % (self.global_options['domain']), 'no', 'regex to match for adding results to the database')
        self.register_option('nameserver', '8.8.8.8', 'yes', 'ip address of a valid nameserver')
        self.register_option('timeout', 2, 'yes', 'maximum lifetime of dns queries')
        self.info = {
                     'Name': 'Reverse Resolver',
                     'Author': 'John Babio (@3vi1john)',
                     'Description': 'Does a reverse lookup of IP address to hostname for the given netblock.',
                     }

    def module_run(self):
        addresses = self.cidr_to_list(self.options['netblock'])
        regex = self.options['regex']
        resolver = dns.resolver.get_default_resolver()
        resolver.nameservers = [self.options['nameserver']]
        resolver.lifetime = self.options['timeout']
        #resolver.timeout = 2
        cnt = 0
        new = 0
        for address in addresses:
            try:
                addr = dns.reversename.from_address(address)
                hosts = resolver.query(addr,'PTR')
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                self.verbose('%s => No record found.' % (address))
            except dns.resolver.Timeout:
                self.verbose('%s => Request timed out.' % (address))
            except (dns.resolver.NoNameservers):
                self.error('Invalid nameserver.')
                return
            for host in hosts:
                host = str(host)[:-1] # slice the trailing dot
                if not regex or re.search(regex, host):
                    new += self.add_host(host, address)
                cnt += 1
                self.alert('%s => %s' % (address, host))

        self.output('%d total hosts found.' % (cnt))
        if new: self.alert('%d NEW hosts found!' % (new))
