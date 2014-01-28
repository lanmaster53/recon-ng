import framework
# unique to module
import dns.resolver

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.register_option('nameserver', '8.8.8.8', 'yes', 'ip address of a valid nameserver')
        self.register_option('overwrite', False, 'yes', 'overwrite exisitng ip addresses')
        self.info = {
                     'Name': 'Hostname Resolver',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Resolves the IP addresses for the hosts from the \'hosts\' table of the database and updates the \'hosts\' table with the results.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]'
                                  'Note: Nameserver must be in IP form.']
                     }

    def module_run(self):
        overwrite = self.options['overwrite']
        q = dns.resolver.get_default_resolver()
        q.nameservers = [self.options['nameserver']]
        q.lifetime = 3
        hosts = self.get_source(self.options['source'], 'SELECT DISTINCT host FROM hosts ORDER BY host' if overwrite else 'SELECT DISTINCT host FROM hosts WHERE ip_address IS NULL ORDER BY host')

        for host in hosts:
            found = False
            try:
                answers = q.query(host)
                for answer in answers:
                    self.add_host(host, answer.address)
                    found = True
                    self.output('%s => %s' % (host, answer.address))
                if found: self.query('DELETE FROM hosts WHERE host=? and ip_address IS NULL', (host,))
            except dns.exception.SyntaxError:
                self.error('Nameserver must be in IP form.')
                return
            except dns.resolver.NXDOMAIN:
                message = 'Unknown'
            except dns.resolver.NoAnswer:
                message = 'No answer'
            except (dns.resolver.NoNameservers, dns.resolver.Timeout):
                message = 'DNS Error'
            if not found: self.verbose('%s => %s' % (host, message))
