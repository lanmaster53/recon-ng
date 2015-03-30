from recon.core.module import BaseModule
import os
import dns
import re

class Module(BaseModule):

    meta = {
        'name': 'DNS Cache Snooper',
        'author': 'thrapt (thrapt@gmail.com)',
        'description': 'Uses the DNS cache snooping technique to check for visited domains',
        'comments': (
            'Nameserver must be in IP form.',
            'http://304geeks.blogspot.com/2013/01/dns-scraping-for-corporate-av-detection.html',
        ),
        'options': (
            ('nameserver', None, True, 'IP address of authoritative nameserver'),
            ('domains', os.path.join(BaseModule.data_path, 'av_domains.lst'), True, 'file containing the list of domains to snoop for'),
        ),
    }

    def module_run(self):
        nameserver = self.options['nameserver']
        with open(self.options['domains']) as fp:
            domains = [x.strip() for x in fp.read().split()]
        for domain in domains:
            response = None
            # prepare our query
            query = dns.message.make_query(domain, dns.rdatatype.A, dns.rdataclass.IN)
            # unset the Recurse flag 
            query.flags ^= dns.flags.RD
            response = dns.query.udp(query, nameserver)
            if len(response.answer) > 0:
                self.alert('%s => Snooped!' % (domain))
            else:
                self.verbose('%s => Not Found.' % (domain))
