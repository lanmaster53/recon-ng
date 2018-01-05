from recon.core.module import BaseModule
import json

class Module(BaseModule):

    meta = {
        'name': 'SSL SAN Lookup',
        'author': 'Zach Grace (@ztgrace) zgrace@403labs.com and Bryan Onel (@BryanOnel86) onel@oneleet.com',
        'description': 'Uses the ssltools.com API to obtain the Subject Alternative Names for a domain. Updates the \'hosts\' table with the results.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        for domain in domains:
            self.heading(domain, level=0)
            url = 'http://www.ssltools.com/api/scan'
            resp = self.request(url, method="POST", payload={'url': domain})
            if not resp.json['response']:
                self.output('SSL endpoint not reachable or response invalid for \'%s\'' % domain)
                continue
            if not resp.json['response']['san_entries']:
                self.output('No Subject Alternative Names found for \'%s\'' % domain)
                continue
            hosts = [x.strip() for x in resp.json['response']['san_entries'] if '*' not in x]
            for host in hosts:
                self.add_hosts(host)
