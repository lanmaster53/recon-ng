from recon.core.module import BaseModule
from recon.mixins.resolver import ResolverMixin
import dns.resolver

class Module(BaseModule, ResolverMixin):

    meta = {
        'name': 'Mail eXchange (MX) and Sender Policy Framework (SPF) Record Retriever',
        'author': 'Jim Becher (@jimbecher, jbecher@korelogic.com)',
        'description': 'Retrieves the MX and SPF IPv4 records for a domain. Updates the \'hosts\' and/or \'netblocks\' tables with the results.',
        'comments': (
            'This module reads domains from the domains table and retrieves the hostnames of the MX records associated with each domain. The hostnames are then stored in the hosts table. It also retrieves the IP addresses and/or netblocks of the SPF records associated with each domain. The addresses are then stored in the hosts and/or netblocks table.',
        ),
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        max_attempts = 3
        resolver = self.get_resolver()
        answers = ""
        for domain in domains:
            attempt = 0
            self.verbose('Retrieving MX records for %s.' % (domain))
            while attempt < max_attempts:
                try:
                    answers = resolver.query(domain, 'MX')
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    self.verbose('%s => No record found.' % (domain))
                except dns.resolver.Timeout:
                    self.verbose('%s => Request timed out.' % (domain))
                    attempt += 1
                    continue
                except (dns.resolver.NoNameservers):
                    self.verbose('%s => Invalid nameserver.' % (domain))
                else:
                    for rdata in answers:
                        host = rdata.exchange
                        host = str(host)
                        host = host[:-1]
                        self.add_hosts(host)
                # break out of the loop
                attempt = max_attempts
        # Now look for SPF records
        for domain in domains:
            attempt = 0
            self.verbose('Retrieving SPF records for %s.' % (domain))
            while attempt < max_attempts:
                try:
                    answers = resolver.query(domain, 'TXT')
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    self.verbose('%s => No record found.' % (domain))
                except dns.resolver.Timeout:
                    self.verbose('%s => Request timed out.' % (domain))
                    attempt += 1
                    continue
                except (dns.resolver.NoNameservers):
                    self.verbose('%s => Invalid nameserver.' % (domain))
                else:
                    for txtrecord in answers:
                        self.verbose('TXT record: %s' % (txtrecord))
                        if "v=spf" in txtrecord.to_text():
                            resp = txtrecord.to_text()
                            words = resp.split()
                            for item in words:
                                if "ip4" in item:
                                    ipaddr = item.split(':', 1)[1]
                                    if "/" in ipaddr:
                                        self.add_netblocks(ipaddr)
                                    else:
                                        self.add_hosts(ip_address=ipaddr)
                                elif "a:" in item:
                                    spfhost = item.split(':', 1)[1]
                                    self.add_hosts(host=spfhost)
                # break out of the loop
                attempt = max_attempts

