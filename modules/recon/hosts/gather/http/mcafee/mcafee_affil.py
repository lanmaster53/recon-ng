import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', 'www.google.com', 'yes', 'target host')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.classify = 'passive'
        self.info = {
                     'Name': 'McAfee Domain Affiliation Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks mcafee.com site for other domains affiliated with a domain.',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.mcafee_affil()

    def mcafee_affil(self):
        verbose = self.options['verbose']['value']
        host = self.options['host']['value']

        url = 'http://www.mcafee.com/threat-intelligence/jsproxy/domain.ashx?q=affiliation&f=%s' % (host)
        if verbose: self.output('URL being retrieved: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return

        # Output the results in table format
        tdata = [] 
        tdata.append(['Domain/URL', 'Category', 'Links'])
        for col in resp.json:
            tdata.append([col['label'], col['hover'], str(col['link'])]) 
        self.table(tdata, True)