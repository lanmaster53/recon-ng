import framework
# unique to module
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('host', self.global_options['domain'], 'yes', 'fully qualified target hostname')
        self.info = {
                     'Name': 'ASP Security Analyzer',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Scans a given host for ASP security configuration vulnerabilities with ASafaWeb (Automated Security Analyser for ASP.NET Websites). https://asafaweb.com/',
                     'Comments': []
                     }
   
    def module_run(self):
        host  = self.options['host']

        # request the scan
        details = [['Check', 'Status']]
        configs = []
        url = 'https://asafaweb.com/Scan?Url=%s' % (host)
        self.verbose('URL: %s' % url)
        resp = self.request(url)

        # extract results
        content = resp.text
        result = re.search(r'<div class="statusSummary" id="StatusSummary">(.*?)</div>', content, re.S)
        # store results
        if result:
            configs = re.findall(r'">(.+?)</', result.group(1), re.S)
        if configs:
            for config in configs:
                check = config.split(':')[0].strip()
                status = config.split(':')[1].strip()
                details.append([check, status])

        # Output the results in table format
        if len(details) > 1:
            self.table(details, True)
        else:
            self.output('No results found.')
