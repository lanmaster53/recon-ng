from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'ThreatMiner DNS lookup',
        'author': 'Pedro Rodrigues',
        'description': 'Use ThreatMiner API to discover subdomains.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        for domain in domains:
            self.heading(domain, level=0)
            resp = self.request(url = 'https://api.threatminer.org/v2/domain.php?rt=5&q=%s' % domain)
            if resp.json.get('status_code') == '200':
                for subdomain in resp.json.get('results'):
                    self.add_hosts(host=subdomain)
