from recon.core.module import BaseModule

class Module(BaseModule):
    meta = {
        'name': 'HackerTarget Lookup',
        'author': 'Michael Henriksen (@michenriksen)',
        'description': 'Uses the HackerTarget.com API to find host names. Updates the \'hosts\' table with the results.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        for domain in domains:
            self.heading(domain, level=0)
            url = 'https://api.hackertarget.com/hostsearch/'
            payload = {'q': domain}
            resp = self.request(url, payload=payload)
            if resp.status_code is not 200:
                self.error('Got unexpected response code: %i' % resp.status_code)
                continue
            if resp.text == '':
                self.output('No results found.')
                continue
            if resp.text.startswith('error'):
                self.error(resp.text)
                continue
            for line in resp.text.split("\n"):
                line = line.strip()
                if line == '':
                    continue
                host, address = line.split(",")
                self.add_hosts(host=host, ip_address=address)
