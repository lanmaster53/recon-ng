import framework
# unique to module
import dns.resolver

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.options = {
                        'nameserver': '8.8.8.8'
                        }
        self.info = {
                     'Name': 'Hostname Resolver',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Resolves the IP address for all of the hosts stored in the database.',
                     'Comments': [
                                  'Note: Nameserver must be in IP form.']
                     }

    def do_run(self, params):
        self.resolve_hosts()
    
    def resolve_hosts(self):
        q = dns.resolver.get_default_resolver()
        q.nameservers = [self.options['nameserver']]
        hosts = self.query('SELECT rowid, host FROM hosts ORDER BY host')
        for host in hosts:
            row = host[0]
            host = host[1]
            try:
                answers = q.query(host)
                address = answers[0].address
            except KeyboardInterrupt:
                print ''
                return
            except dns.resolver.NXDOMAIN: address = 'unknown'
            except dns.resolver.NoAnswer: address = 'no answer'
            except dns.exception.SyntaxError:
                self.error('Nameserver must be in IP form.')
                return
            except: address = 'error'
            self.output('%s => %s' % (host, address))
            self.query('UPDATE hosts SET address="%s" WHERE rowid="%s"' % (address, row))