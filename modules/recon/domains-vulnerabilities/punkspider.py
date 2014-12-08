import module
# unique to module
from datetime import datetime
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
            'Name': 'PunkSPIDER Vulnerabilty Finder',
            'Author': 'Tim Tomes (@LaNMaSteR53) and thrapt (thrapt@gmail.com)',
            'Description': 'Leverages PunkSPIDER to search for previosuly discovered vulnerabltiies on hosts within a domain.'
        }
   
    def module_run(self, domains):
        vuln_types = ['bsqli', 'sqli', 'xss', 'trav', 'mxi', 'osci', 'xpathi']
        url = 'http://punkspider.hyperiongray.com/service/search/domain/'
        for domain in domains:
            self.heading(domain, level=0)
            payload = {'searchKey': 'url', 'searchValue': '"%s"' % (domain), 'filterType': 'OR'}
            payload['filters'] = vuln_types
            vulnerable = False
            page = 1
            while True:
                payload['pageNumber'] = page
                resp = self.request(url, method='POST', payload=payload, content='json')
                results = resp.json['output']['domainSummaryDTOs']
                if not results: break
                for result in results:
                    #if any([result[x] for x in vuln_types]):
                    data = {}
                    data['host'] = re.search('//(.+?)/', result['id']).group(1)
                    data['reference'] = 'http://punkspider.hyperiongray.com/service/search/detail/%s' % ('.'.join(data['host'].split('.')[::-1]))
                    resp = self.request(data['reference'])
                    vulns = resp.json['data']
                    for vuln in vulns:
                        vulnerable = True
                        data['publish_date'] = datetime.strptime(result['timestamp'], '%a %b %d %H:%M:%S %Z %Y')
                        data['category'] = vuln['bugType'].upper()
                        data['status'] = 'unknown'
                        data['example'] = vuln['vulnerabilityUrl']
                        for key in sorted(data.keys()):
                            self.output('%s: %s' % (key.title(), data[key]))
                        print(self.ruler*50)
                        self.add_vulnerabilities(**data)
                page += 1
            if not vulnerable:
                self.output('No vulnerabilites found.')
