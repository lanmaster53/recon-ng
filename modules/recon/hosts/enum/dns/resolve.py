import framework
# unique to module
import dns.resolver

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('nameserver', '8.8.8.8', 'yes', 'ip address of a valid nameserver')
        self.info = {
                     'Name': 'Hostname Resolver',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Resolves the IP addresses for the hosts from the \'hosts\' table of the database and updates the \'hosts\' table with the results.',
                     'Comments': [
                                  'Note: Nameserver must be in IP form.']
                     }

    def module_run(self):
        q = dns.resolver.get_default_resolver()
        q.nameservers = [self.options['nameserver']['value']]
        q.lifetime = 3
        hosts = self.query('SELECT rowid, host FROM hosts ORDER BY host')
        for host in hosts:
            row = host[0]
            host = host[1]
            try:
                answers = q.query(host)
                address = answers[0].address
                self.query('UPDATE hosts SET ip_address=\'%s\' WHERE rowid=\'%s\'' % (address, row))
            except KeyboardInterrupt:
                print ''
                return
            except dns.exception.SyntaxError:
                self.error('Nameserver must be in IP form.')
                return
            except dns.resolver.NXDOMAIN:
                address = 'Unknown'
            except dns.resolver.NoAnswer:
                address = 'No answer'
            except (dns.resolver.NoNameservers, dns.resolver.Timeout):
                address = 'Error'
            self.output('%s => %s' % (host, address))
