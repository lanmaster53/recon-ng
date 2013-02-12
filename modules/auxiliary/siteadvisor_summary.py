import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'passive'
        self.info = {
                     'Name': 'McAfee SiteAdvisor Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks siteadvisor.com site for links and other information with domains.',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.siteadv_summ()

    def siteadv_summ(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']

        url = 'http://www.siteadvisor.com/sites/%s' % (domain)
        if verbose: self.output('URL being retrieved: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return

        # Get the overall security results
        sec_results = re.findall(r'class="results">(.+)</p>', resp.text)
        tdata_sec = [] 
        tdata_sec.append(['Security Results'])
        
        # Get country of origin and number of users
        finding_country = re.search(r'img src="/images/countryflags.+p> (.+)</td', resp.text)
        finding_visitors = re.search(r'img src="/images/visitor.+p>(.+)</td', resp.text)
        tdata_sec.append(['Country: ' + finding_country.group(1) + '                Visitors: ' + finding_visitors.group(1)])
        tdata_sec.append([' '])
        
        # Line wrapping for long paragraph that breaks table formatting
        paraMaxLen = 80
        paraLen = len(sec_results[0])
        if paraLen > paraMaxLen:
            wrappedLines = []
            for line in sec_results[0].split('\n'):
                while True:
                    wrappedLines.append(line[:paraMaxLen])
                    line = line[paraMaxLen:]
                    if not line: break
            for item in wrappedLines:
                tdata_sec.append([item])
        self.table(tdata_sec, True)
    
        # Get the sites this domain's web site links to
        finding = re.findall(r"area shape.+title='(.+)' onMouse", resp.text)
        finding.sort()
        tdata = [] 
        tdata.append(['Domain(s) Linked to'])
        for domain in finding:
            tdata.append([domain])
        self.table(tdata, True)
