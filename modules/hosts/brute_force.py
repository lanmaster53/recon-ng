import _cmd
# unique to module
import dns.resolver
import os.path

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'domain': self.goptions['domain'],
                        'wordlist': './data/wordlist.txt',
                        'nameserver': '8.8.8.8'
                        }
        self.info = {
                     'Name': 'DNS Hostname Brute Forcer',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Brute forces host names for the given domain using the DNS nameserver and wordlist provided.',
                     'Comments': []
                     }

    def do_run(self, params):
        self.brute_hosts()
    
    def brute_hosts(self):
        q = dns.resolver.get_default_resolver()
        q.nameservers = [self.options['nameserver']]
        fake_host = 'sudhfydgssjdue.%s' % (self.options['domain'])
        cnt, tot = 0, 0
        try:
            answers = q.query(fake_host)
            self.output('Wildcard DNS entry found. Cannot brute force hostnames.')
            return
        except KeyboardInterrupt:
            print ''
            return
        except dns.resolver.NXDOMAIN:
            if self.goptions['verbose']: self.output('No Wildcard DNS entry found. Attempting to brute force DNS records.')
            pass
        if os.path.exists(self.options['wordlist']):
            words = open(self.options['wordlist']).read().split()
            for word in words:
                host = '%s.%s' % (word, self.options['domain'])
                try: answers = q.query(host)
                except KeyboardInterrupt:
                    print ''
                    break
                except dns.resolver.NXDOMAIN:
                    if self.goptions['verbose']: self.output('%s => Not a host.' % (host))
                    continue
                self.alert('%s => Host found!' % (host))
                tot += 1
                cnt += self.add_host(host)
            self.output('%d total hosts found.' % (tot))
            if cnt: self.alert('%d NEW hosts found!' % (cnt))
        else:
            self.error('Wordlist file not found.')