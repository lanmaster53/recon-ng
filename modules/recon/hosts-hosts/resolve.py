import module
# unique to module
import dns.resolver

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL AND ip_address IS NULL')
        self.info = {
                     'Name': 'Hostname Resolver',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Resolves the IP address for a host. Updates the \'hosts\' table with the results.',
                     'Comments': [
                                  'Note: Nameserver must be in IP form.'
                                  ]
                     }

    def module_run(self, hosts):
        q = self.get_resolver()
        for host in hosts:
            found = False
            try:
                answers = q.query(host)
                for answer in answers:
                    self.add_hosts(host, answer.address)
                    found = True
                    self.output('%s => %s' % (host, answer.address))
                if found: self.query('DELETE FROM hosts WHERE host=? and ip_address IS NULL', (host,))
            except dns.resolver.NXDOMAIN:
                message = 'Unknown'
            except dns.resolver.NoAnswer:
                message = 'No answer'
            except (dns.resolver.NoNameservers, dns.resolver.Timeout):
                message = 'DNS Error'
            if not found: self.verbose('%s => %s' % (host, message))
