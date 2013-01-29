import framework
# unique to module
import os
import dns
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('nameserver', '', 'yes', 'ip address of nameserver')
        self.register_option('domains', 'default', 'yes', 'list of domains to check')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'DNS cache snooping',
                     'Author': 'thrapt (thrapt@gmail.com)',
                     'Description': 'Uses the DNS cache snooping technique to check for visited domains',
                     'Comments': [
                                  'Based on the work of 304geeks.com',
                                  'http://304geeks.blogspot.com/2013/01/dns-scraping-for-corporate-av-detection.html',
                                  '',
                                  'domains options: default, <hostname>, <path/to/infile>',
                                  'Nameserver must be in IP form.'
                                 ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.cachesnoop()

    def cachesnoop(self):
        verbose = self.options['verbose']['value']
        domains = self.options['domains']['value']
        nameserver = self.options['nameserver']['value']
        
        if domains == 'default': domains = 'data/domains-scrape.lst'
        if os.path.exists(domains): hosts = open(domains).read().split()
        else: hosts = [domains]
        
        self.output('Starting queries...')
        
        for host in hosts:
            # prepare our query
            query = dns.message.make_query(host, dns.rdatatype.A, dns.rdataclass.IN)
            # unset the Recurse flag 
            query.flags ^= dns.flags.RD
            try:
                # try the query
                response = dns.query.udp(query, nameserver)
            except KeyboardInterrupt:
                print ''
                return
            except dns.resolver.NXDOMAIN: 
                self.output('%s => Unknown', host)
                return
            except dns.resolver.NoAnswer: 
                self.output('%s => No answer', nameserver)
                return
            except dns.exception.SyntaxError:
                self.error('Nameserver must be in IP form.')
                return
            except: response = 'error'

            # searchs the response to find the answer
            response = re.findall(r';ANSWER\s^(?=(?!;))(.*)$', str(response), re.MULTILINE)
            
            if len(response) > 0:
                ip = response[0].split()[-1]
                self.output('%s %s' % (host.ljust(50), ip))
            else:
                if verbose: self.output('%s not found' % (host.ljust(50)))
