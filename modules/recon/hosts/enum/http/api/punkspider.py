import module
# unique to module
import urllib
import json
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
        cnt = 0
        new = 0
        self.output('Gathering vulnerability scan data...')
        for domain in domains:
            self.heading(domain, level=0)
            payload = {'searchKey': 'url', 'searchValue': '"%s"' % (domain), 'filterType': 'OR'}
            payload['filters'] = vuln_types
            vulnerable = False
            page = 1
            while True:
                payload['pageNumber'] = page
                resp = self.request(url, method='POST', payload=payload, content='json')
                jsonobj = resp.json
                results = jsonobj['output']['domainSummaryDTOs']
                if not results: break
                for result in results:
                    #if any([result[x] for x in vuln_types]):
                    hostname = re.search('//(.+?)/', result['id']).group(1)
                    vuln_path = '.'.join(hostname.split('.')[::-1])
                    vuln_url = 'http://punkspider.hyperiongray.com/service/search/detail/%s' % (vuln_path)
                    resp = self.request(vuln_url)
                    jsonobj = resp.json
                    vulns = jsonobj['data']
                    for vuln in vulns:
                        vulnerable = True
                        category = vuln['bugType'].upper()
                        self.output('Host: %s' % (hostname))
                        self.output('Attack: %s' % (vuln['vulnerabilityUrl']))
                        self.output('Parameter: %s' % (vuln['parameter']))
                        self.output('Published: %s' % (result['timestamp']))
                        self.output('Category: %s' % (category))
                        print(self.ruler*50)
                        new += self.add_vulnerabilities(hostname, 'http://punkspider.hyperiongray.com/', vuln['vulnerabilityUrl'], result['timestamp'], category)
                        cnt += 1
                page += 1
            if not vulnerable:
                self.output('No vulnerabilites found.')
        self.summarize(new, cnt)
