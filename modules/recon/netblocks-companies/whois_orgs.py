from recon.core.module import BaseModule
from urlparse import urlparse

class Module(BaseModule):

    meta = {
        'name': 'Whois Company Harvester',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Uses the ARIN Whois RWS to harvest Companies data from whois queries for the given netblock. Updates the \'companies\' table with the results.',
        'query': 'SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL',
    }

    def module_run(self, netblocks):
        headers = {'Accept': 'application/json'}
        for netblock in netblocks:
            self.heading(netblock, level=0)
            urls = [
                'http://whois.arin.net/rest/cidr/%s' % (netblock),
                'http://whois.arin.net/rest/ip/%s' % (netblock.split('/')[0]),
            ]
            for url in urls:
                self.verbose('URL: %s' % url)
                resp = self.request(url, headers=headers)
                if 'No record found for the handle provided.' in resp.text:
                    self.output('No companies found.')
                    continue
                for ref in ['orgRef', 'customerRef']:
                    if ref in resp.json['net']:
                        company = resp.json['net'][ref]['@name']
                        handle = resp.json['net'][ref]['$']
                        self.add_companies(company=company, description=handle)
