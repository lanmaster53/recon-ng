import framework
# unique to module
import dns.resolver
import os.path

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('wordlist', './data/hostnames.txt', 'yes', 'path to hostname wordlist')
        self.register_option('nameserver', '8.8.8.8', 'yes', 'ip address of a valid nameserver')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'active'
        self.info = {
                     'Name': 'DNS Hostname Brute Forcer',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Brute forces host names using DNS. This module updates the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.brute_hosts()
    
    def brute_hosts(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']
        wordlist = self.options['wordlist']['value']
        q = dns.resolver.get_default_resolver()
        q.nameservers = [self.options['nameserver']['value']]
        fake_host = 'sudhfydgssjdue.%s' % (domain)
        cnt, tot = 0, 0
        try:
            answers = q.query(fake_host)
            self.output('Wildcard DNS entry found. Cannot brute force hostnames.')
            return
        except KeyboardInterrupt:
            print ''
            return
        except dns.resolver.NXDOMAIN:
            if verbose: self.output('No Wildcard DNS entry found. Attempting to brute force DNS records.')
            pass
        if os.path.exists(wordlist):
            words = open(wordlist).read().split()
            for word in words:
                host = '%s.%s' % (word, domain)
                try: answers = q.query(host, 'A')
                except KeyboardInterrupt:
                    print ''
                    break
                except dns.resolver.NXDOMAIN:
                    if verbose: self.output('%s => Not a host' % (host))
                    continue
                except dns.resolver.NoAnswer:
                    if verbose: self.output('%s => No answer' % (host))
                    continue
                for answer in answers.response.answer:
                    for rdata in answer:
                        if rdata.rdtype == 1:
                            self.alert('%s => Host found!' % (host))
                            cnt += self.add_host(host)
                            tot += 1
                        if rdata.rdtype == 5:
                            cname = rdata.target.to_text()[:-1]
                            self.alert('%s => Host found!' % (cname))
                            cnt += self.add_host(cname)
                            tot += 1
            self.output('%d total hosts found.' % (tot))
            if cnt: self.alert('%d NEW hosts found!' % (cnt))
        else:
            self.error('Wordlist file not found.')