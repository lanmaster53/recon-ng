import framework
# unique to module
import dns.resolver
import os.path
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.global_options['domain']['value'], 'yes', self.global_options['domain']['desc'])
        self.register_option('regex', '%s$' % (self.global_options['domain']['value']), 'no', 'regex to match for adding results to the database')
        self.register_option('suffix_wordlist', './data/tlds-alpha-by-domain.txt', 'yes', 'path to public suffix wordlist')
        self.register_option('nameserver', '8.8.8.8', 'yes', 'ip address of a valid nameserver')
        self.register_option('attempts', 3, 'yes', 'Number of retry attempts per host')
        self.info = {
                     'Name': 'DNS Public Suffix Brute Forcer',
                     'Author': 'Marcus Watson (@BranMacMuffin)',
                     'Description': 'Brute forces host name TLDs using DNS and updates the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }

    def __remove_suffix__(self, domain, suffix_words):

        if "." not in domain:
            return domain

        lower_domain = domain.lower()

        found_suffix = ""

        for word in suffix_words:
            if lower_domain.endswith("."+word) and len(word)>len(found_suffix):
                found_suffix = word

        return domain[:len(domain)-len(found_suffix)-1]					 
					 
    def __retrieve_suffix_list__(self, suffix_wordlist):
        with open(suffix_wordlist) as f:
                return {line.strip().lower() for line in f if len(line)>0 and line[0] is not '#'}

    def module_run(self):
        domain = self.options['domain']

        regex = self.options['regex']
        suffix_wordlist = self.options['suffix_wordlist']
        max_attempts = self.options['attempts']
        resolver = dns.resolver.get_default_resolver()
        resolver.nameservers = [self.options['nameserver']]
        resolver.lifetime = 2
        #resolver.timeout = 2
        cnt = 0
        new = 0

        self.verbose('Attempting to brute force DNS Public Suffix records.')

        if os.path.exists(suffix_wordlist) == False:
            self.error('TLD wordlist file not found.')
            return

        words = self.__retrieve_suffix_list__(suffix_wordlist)
        domain_less_suffix = self.__remove_suffix__(domain, words)

        for word in words:

            attempt = 0

            while attempt < max_attempts:
                host = '%s.%s' % (domain_less_suffix, word)
                try:
                    answers = resolver.query(host)
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                    self.verbose('%s => No record found.' % (host))
                except dns.resolver.Timeout:
                    self.verbose('%s => Request timed out.' % (host))
                    attempt += 1
                    continue
                else:
                    # process answers
                    for answer in answers.response.answer:
                        for rdata in answer:
                            if rdata.rdtype in (1, 5):
                                if rdata.rdtype == 1:
                                    self.alert('%s => (A) %s - Host found!' % (host, host))
                                    cnt += 1
                                if rdata.rdtype == 5:
                                    cname = rdata.target.to_text()[:-1]
                                    self.alert('%s => (CNAME) %s - Host found!' % (host, cname))
                                    if not regex or re.search(regex, cname): new += self.add_host(cname)
                                    cnt += 1
                                # add the host in case a CNAME exists without an A record
                                if not regex or re.search(regex, host): new += self.add_host(host)
                # break out of the loop
                attempt = max_attempts
        self.output('%d total hosts found.' % (cnt))

        if new: self.alert('%d NEW hosts found!' % (new))

