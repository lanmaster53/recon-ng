import framework
# unique to module
import re
from datetime import date

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.info = {
                     'Name': 'Web Archive Lookup',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Checks web.archive.org for archived versions of web pages on the given domain.',
                     'Comments': []
                     }
   
    def module_run(self):
        domain  = self.options['domain']['value']

        # Get the first year the domain was archived
        url = 'http://web.archive.org/web/*/%s' % (domain)
        self.verbose('URL: %s' % url)
        resp = self.request(url)
        content = resp.text
        match = re.search(r'way back to <[^>]+>[A-Z][a-z]+ \d+, ([\d]{4})<\/a>', content)

        if match:
            first_year = match.group(1)
        else:
            self.output('No results found')
            return

        # iterate through years until this year
        details = [['Date', 'URL']]
        cnt = 0
        for year in range(int(first_year), date.today().year+1):
            url = 'http://web.archive.org/web/%s0201000000*/%s' % (str(year), domain)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            content = resp.text
            results = re.findall(r'<div class="day">\s+<a (href="[^>]+>)', content)

            # store results
            if results:
                for result in results:
                    finding_url  = re.search(r"(/web/[0-9]+/[^\"]+)", result).group(1)
                    finding_date = re.search(r'class="(.+)">', result).group(1)
                    details.append([finding_date, 'web.archive.org'+finding_url])
                    cnt += 1

        # output the results in table format
        if len(details) > 1:
            self.table(details, True)
            self.output('%d archives found.' % (cnt))
        else:
            self.output('No results found')
