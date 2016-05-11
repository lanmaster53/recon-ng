from recon.core.module import BaseModule
from datetime import datetime
import re

class Module(BaseModule):

    meta = {
        'name': 'PunkSPIDER Vulnerabilty Finder',
        'author': 'Tim Tomes (@LaNMaSteR53) and thrapt (thrapt@gmail.com)',
        'description': 'Leverages the PunkSPIDER API to search for previosuly discovered vulnerabltiies on hosts within a domain.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }
   
    def module_run(self, domains):
        vuln_types = ['bsqli', 'sqli', 'xss', 'trav', 'mxi', 'osci', 'xpathi']
        url = 'https://punkspider.hyperiongray.com/service/search/domain/'
        for domain in domains:
            self.heading(domain, level=0)
            payload = {'searchKey': 'url', 'searchValue': domain, 'filterType': 'OR'}
            payload['filters'] = vuln_types
            vulnerable = False
            page = 1
            while True:
                payload['pageNumber'] = page
                resp = self.request(url, method='POST', payload=payload, content='json')
                results = resp.json['output']['domainSummaryDTOs']
                if not results: break
                for result in results:
                    data = {}
                    data['host'] = result['id']
                    data['reference'] = 'https://punkspider.hyperiongray.com/service/search/detail/%s' % ('.'.join(data['host'].split('.')[::-1]))
                    resp = self.request(data['reference'])
                    vulns = resp.json['data']
                    for vuln in vulns:
                        vulnerable = True
                        data['example'] = vuln['vulnerabilityUrl']
                        data['publish_date'] = datetime.strptime(result['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
                        data['category'] = vuln['bugType'].upper()
                        data['status'] = None
                        self.add_vulnerabilities(**data)
                page += 1
            if not vulnerable:
                self.output('No vulnerabilites found.')
