import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', self.goptions['domain']['value'], 'yes', 'fully qualified target hostname')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'ASP Security Analyzer',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Scans a given host for ASP security configuration vulnerabilities with ASafaWeb (Automated Security Analyser for ASP.NET Websites). https://asafaweb.com/',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.asafaweb()

    def asafaweb(self):
        verbose = self.options['verbose']['value']
        host  = self.options['host']['value']

        # request the scan
        details = [['Check', 'Status']]
        url = 'https://asafaweb.com/Scan?Url=%s' % (host)
        if verbose: self.output('URL for asafaweb.com: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return

        # extract results
        content = resp.text
        result = re.search(r'<div class="statusSummary" id="StatusSummary">(.*?)</div>', content, re.S)
        # store results
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
            self.output('No results found')
