import module
# unique to module
import dns.resolver
import os.path

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL')
        self.register_option('suffixes', self.data_path+'/suffixes.txt', True, 'path to public suffix wordlist')
        self.info = {
                     'Name': 'DNS Public Suffix Brute Forcer',
                     'Author': 'Marcus Watson (@BranMacMuffin)',
                     'Description': 'Brute forces TLDs and SLDs using DNS. Updates the \'domains\' table with the results.',
                     'Comments': [
                                  'TLDs: https://data.iana.org/TLD/tlds-alpha-by-domain.txt',
                                  'SLDs: https://raw.github.com/gavingmiller/second-level-domains/master/SLDs.csv'
                                  ]
                     }

    def module_run(self, domains):
        suffix_wordlist = self.options['suffixes']
        max_attempts = 3
        resolver = self.get_resolver()
        cnt = 0
        new = 0
        if os.path.exists(suffix_wordlist):
            with open(suffix_wordlist) as f:
                words = [line.strip().lower() for line in f if len(line)>0 and line[0] is not '#']
            for domain in domains:
                self.heading(domain, level=0)
                domain_root = domain.split('.')[0]
                for word in words:
                    attempt = 0
                    while attempt < max_attempts:
                        domain = '%s.%s' % (domain_root, word)
                        try:
                            answers = resolver.query(domain, 'SOA')
                        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                            self.verbose('%s => No record found.' % (domain))
                        except dns.resolver.Timeout:
                            self.verbose('%s => Request timed out.' % (domain))
                            attempt += 1
                            continue
                        else:
                            # process answers
                            for answer in answers.response.answer:                                        
                                if answer.rdtype == 6:
                                    soa = answer.name.to_text()[:-1]
                                    self.alert('%s => (SOA) %s - Host found!' % (domain, soa))
                                    cnt += 1
                                    # use "host" rather than "soa" as sometimes the SOA record has a CNAME
                                    new += self.add_domains(domain)
                        # break out of the loop
                        attempt = max_attempts
            self.summarize(new, cnt)
        else:
            self.error('Suffix wordlist file (\'%s\') not found.' % (suffix_wordlist))
