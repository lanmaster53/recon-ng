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
        self.register_option('attempts', 3, 'yes', 'Number of retry attempts per host')
        self.info = {
                     'Name': 'DNS Hostname Brute Forcer',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Brute forces host names using DNS and updates the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }

    def module_run(self):
        domain = self.options['domain']['value']
        wordlist = self.options['wordlist']['value']
        max_attempts = self.options['attempts']['value']
        q = dns.resolver.get_default_resolver()
        q.nameservers = [self.options['nameserver']['value']]
        q.lifetime = 3
        q.timeout = 2
        fake_host = 'sudhfydgssjdue.%s' % (domain)
        cnt, tot = 0, 0
        try:
            answers = q.query(fake_host)
            self.output('Wildcard DNS entry found. Cannot brute force hostnames.')
            return
        except (dns.resolver.NoNameservers, dns.resolver.Timeout):
            self.error('Invalid nameserver.')
            return
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            self.verbose('No Wildcard DNS entry found. Attempting to brute force DNS records.')
            pass
        if os.path.exists(wordlist):
            words = open(wordlist).read().split()
            for word in words:
                attempt = 0
                while attempt < max_attempts:
                    host = '%s.%s' % (word, domain)
                    try:
                        answers = q.query(host)
                    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                        self.verbose('%s => Not a host.' % (host))
                    except dns.resolver.Timeout:
                        self.verbose('%s => Request timed out.' % (host))
                        attempt += 1
                        continue
                    else:
                        # process answers
                        for answer in answers.response.answer:
                            for rdata in answer:
                                if rdata.rdtype == 1:
                                    self.alert('%s => (A) %s - Host found!' % (host, host))
                                    cnt += self.add_host(host)
                                    tot += 1
                                if rdata.rdtype == 5:
                                    cname = rdata.target.to_text()[:-1]
                                    self.alert('%s => (CNAME) %s - Host found!' % (host, cname))
                                    if host != cname:
                                        cnt += self.add_host(cname)
                                        tot += 1
                                    cnt += self.add_host(host)
                                    tot += 1
                    # break out of the loop
                    attempt = max_attempts
            self.output('%d total hosts found.' % (tot))
            if cnt: self.alert('%d NEW hosts found!' % (cnt))
        else:
            self.error('Wordlist file not found.')
