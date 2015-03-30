from recon.core.module import BaseModule
from recon.mixins.resolver import ResolverMixin
import dns.resolver

class Module(BaseModule, ResolverMixin):

    meta = {
        'name': 'Hostname Resolver',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Resolves the IP address for a host. Updates the \'hosts\' table with the results.',
        'comments': (
            'Note: Nameserver must be in IP form.',
        ),
        'query': 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL AND ip_address IS NULL',
    }

    def module_run(self, hosts):
        q = self.get_resolver()
        for host in hosts:
            try:
                answers = q.query(host)
            except dns.resolver.NXDOMAIN:
                self.verbose('%s => Unknown' % (host))
            except dns.resolver.NoAnswer:
                self.verbose('%s => No answer' % (host))
            except (dns.resolver.NoNameservers, dns.resolver.Timeout):
                self.verbose('%s => DNS Error' % (host))
            else:
                for i in range(0, len(answers)):
                    if i == 0:
                        self.query('UPDATE hosts SET ip_address=? WHERE host=?', (answers[i].address, host))
                    else:
                        data = {
                            'host': self.to_unicode(host),
                            'ip_address': self.to_unicode(answers[i].address)
                        }
                        self.insert('hosts', data, data.keys())
                    self.output('%s => %s' % (host, answers[i].address))
