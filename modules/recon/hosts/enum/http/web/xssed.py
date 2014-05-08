import module
# unique to module
import re
import textwrap
import time

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL ORDER BY domain')
        self.info = {
                     'Name': 'XSSed Domain Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks XSSed.com for XSS records associated with a domain and displays the first 20 results.'
                     }
   
    def module_run(self, domains):
        cnt = 0
        new = 0
        for domain in domains:
            self.heading(domain, level=0)
            url = 'http://xssed.com/search?key=%s' % (domain)
            resp = self.request(url)
            content = resp.text
            #if re.search('<b>XSS:</b>', content):
            vulns = re.findall('mirror/([0-9]+)/\' target=\'_blank\'>', content)
            for vuln in vulns:
                # Go fetch and parse the specific page for this item
                url_vuln = 'http://xssed.com/mirror/%s/' % vuln
                resp_vuln = self.request(url_vuln)
                # Parse the response and get the details
                details = re.findall('<th class="row3"[^>]*>[^:?]+[:?]+(.+?)<\/th>', resp_vuln.text)#.replace('&nbsp;', ' '))
                details = [self.html_unescape(x).strip() for x in details]
                status = re.search('([UNFIXED]+)',details[3]).group(1)
                if status == 'UNFIXED':
                    self.output('Mirror: %s' % (url_vuln))
                    self.output('Host: %s' % (details[5]))
                    self.output('Attack: %s' % (textwrap.fill(details[8], 100, initial_indent='', subsequent_indent=self.spacer*2)))
                    self.output('Submitted: %s' % (details[0]))
                    self.output('Published: %s' % (details[1]))
                    self.output('Category: %s' % (details[6]))
                    #self.output('Status: %s' % (status))
                    print(self.ruler*50)
                    new += self.add_vulnerabilities(details[5], url_vuln, details[8], details[1], details[6])
                    cnt += 1
                # results in 503 errors if not throttled
                time.sleep(1)
            if not vulns:
                self.output('No vulnerabilites found.')
        self.summarize(new, cnt)
