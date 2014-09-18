import module
# unique to module
from datetime import datetime
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
            'Name': 'XSSposed Domain Lookup',
            'Author': 'Tim Tomes (@LaNMaSteR53)',
            'Description': 'Checks XSSposed.com for XSS records associated with a domain.'
            }
   
    def module_run(self, domains):
        cnt = 0
        new = 0
        url = 'https://www.xssposed.org/api/1/search/?domain=%s'
        for domain in domains:
            self.heading(domain, level=0)
            resp = self.request(url % (domain))
            vulns = resp.xml.findall('item')
            for vuln in vulns:
                data = {}
                data['host'] = vuln.find('host').text
                data['reference'] = vuln.find('url').text
                data['publish_date'] = datetime.strptime(vuln.find('reporteddate').text, '%a, %d %b %Y %H:%M:%S +0000')
                data['category'] = vuln.find('type').text
                data['status'] = 'unfixed' if vuln.find('fixed').text == '0' else 'fixed'
                resp_vuln = self.request(data['reference'])
                data['example'] = re.search('href="([^"]*%s[^"]*)"' % (data['host']), resp_vuln.text).group(1)
                for key in sorted(data.keys()):
                    self.output('%s: %s' % (key.title(), data[key]))
                print(self.ruler*50)
                new += self.add_vulnerabilities(**data)
                cnt += 1
            if not vulns:
                self.output('No vulnerabilites found.')
        self.summarize(new, cnt)
