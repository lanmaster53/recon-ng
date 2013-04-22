import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.info = {
                     'Name': 'McAfee SiteAdvisor Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks siteadvisor.com for links and other information for the given domain.',
                     'Comments': []
                     }
   
    def module_run(self):
        domain = self.options['domain']['value']

        url = 'http://www.siteadvisor.com/sites/%s' % (domain)
        self.verbose('URL: %s' % url)
        resp = self.request(url)

        # Get the overall security results
        
        
        # Get country of origin and number of users
        country = re.search(r'img src="/images/countryflags.+p> (.+)</td', resp.text)
        visitors = re.search(r'img src="/images/visitor.+p>(.+)</td', resp.text)
        results = re.search(r'class="results">(.+)</p>', resp.text)
        self.output('Country: %s' % (country.group(1)))
        self.output('Visitors: %s' % (visitors.group(1)))
        self.output(results.group(1))
    
        # Get the sites this domain's web site links to
        sites = re.findall(r"area shape.+title='(.+)' onMouse", resp.text)
        tdata = [] 
        tdata.append(['Linked to...'])
        for site in sorted(sites):
            tdata.append([site])
        self.table(tdata, True)
