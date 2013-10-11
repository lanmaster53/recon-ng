import framework
# unique to module
import re
import textwrap
import time

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.info = {
                     'Name': 'XSSed Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks XSSed.com for XSS records for the given domain and displays the first 20 results.',
                     'Comments': []
                     }
   
    def module_run(self):
        domain = self.options['domain']['value']

        url = 'http://xssed.com/search?key=%s' % (domain)
        self.verbose('URL: %s' % url)
        resp = self.request(url)
        content = resp.text

        if re.search('<b>XSS:</b>', content):
            vulns = re.findall('mirror/([0-9]+)/\' target=\'_blank\'>', content)
            for vuln in vulns:
                # Go fetch and parse the specific page for this item
                urlDetail = 'http://xssed.com/mirror/%s/' % vuln
                respDetail = self.request(urlDetail)
                # Parse the response and get the details
                details = re.findall('<th class="row3"[^>]*>(.*?)</th>', respDetail.text)#.replace('&nbsp;', ' '))
                details = [self.html_unescape(x) for x in details]
                status = re.search('([UNFIXED]+)',details[3]).group(1)
                print self.ruler*50
                self.output('Mirror: %s' % (urlDetail))
                self.output(details[5])
                self.output(textwrap.fill(details[8], 100, initial_indent='', subsequent_indent=self.spacer*2))
                self.output(details[0])
                self.output(details[1])
                self.output(details[6])
                self.output('Status: %s' % (status))
                # results in 503 errors if not throttled
                time.sleep(1)
            print self.ruler*50
        else:
            self.output('No results found.')
