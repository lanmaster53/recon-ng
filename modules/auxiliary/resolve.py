import _cmd
# unique to module
import dns.resolver

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'nameserver': '8.8.8.8'
                        }
        self.info = {
                     'Name': 'Hostname Resolver',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Resolves the IP address for all of the hosts stored in the database.',
                     'Comments': []
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
            except dns.resolver.NXDOMAIN:
                address = 'unknown'
            self.output('%s => %s' % (host, address))
            self.query('UPDATE hosts SET address="%s" WHERE rowid="%s"' % (address, row))