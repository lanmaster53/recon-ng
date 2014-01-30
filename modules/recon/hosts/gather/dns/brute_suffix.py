import module
# unique to module
import dns.resolver
import os.path

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', self.global_options.description['domain'])
        self.register_option('suffixes', './data/suffixes.txt', 'yes', 'path to public suffix wordlist')
        self.register_option('nameserver', '8.8.8.8', 'yes', 'ip address of a valid nameserver')
        self.register_option('attempts', 3, 'yes', 'Number of retry attempts per host')
        self.info = {
                     'Name': 'DNS Public Suffix Brute Forcer',
                     'Author': 'Marcus Watson (@BranMacMuffin)',
                     'Description': 'Brute forces host name TLDs and SLDs using DNS and updates the \'hosts\' table of the database with the results.',
                     'Comments': ['TLDs: https://data.iana.org/TLD/tlds-alpha-by-domain.txt',
                                  'SLDs: https://raw.github.com/gavingmiller/second-level-domains/master/SLDs.csv'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']
        suffix_wordlist = self.options['suffixes']
        max_attempts = self.options['attempts']
        resolver = dns.resolver.get_default_resolver()
        resolver.nameservers = [self.options['nameserver']]
        resolver.lifetime = 2
        cnt = 0
        new = 0
        if os.path.exists(suffix_wordlist):
            with open(suffix_wordlist) as f:
                words = [line.strip().lower() for line in f if len(line)>0 and line[0] is not '#']
            domain_root = domain.split('.')[0]
            for word in words:
                attempt = 0
                while attempt < max_attempts:
                    host = '%s.%s' % (domain_root, word)
                    try:
                        answers = resolver.query(host, 'SOA')
                    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                        self.verbose('%s => No record found.' % (host))
                    except dns.resolver.Timeout:
                        self.verbose('%s => Request timed out.' % (host))
                        attempt += 1
                        continue
                    else:
                        # process answers
                        for answer in answers.response.answer:                                        
                            if answer.rdtype == 6:
                                soa = answer.name.to_text()[:-1]
                                self.alert('%s => (SOA) %s - Host found!' % (host, soa))
                                cnt += 1
                                # use "host" rather than "soa" as sometimes the SOA record has a CNAME
                                new += self.add_host(host)
                    # break out of the loop
                    attempt = max_attempts
            self.output('%d total hosts found.' % (cnt))
            if new: self.alert('%d NEW hosts found!' % (new))
        else:
            self.error('Suffix wordlist file (\'%s\') not found.' % (suffix_wordlist))
