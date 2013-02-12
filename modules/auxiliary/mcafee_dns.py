import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.register_option('addhoststodb', False, 'no', 'Add hosts discovered to the database.')
        self.classify = 'passive'
        self.info = {
                     'Name': 'McAfee Domain DNS Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks mcafee.com site for DNS information about a domain. This module can update the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.mcafee_dns()

    def mcafee_dns(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']
        addhosts = self.options['addhoststodb']['value']

        url = 'http://www.mcafee.com/threat-intelligence/jsproxy/domain.ashx?q=dns&f=%s' % (domain)
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
        tdata.append(['Domain', 'Hostname', 'IP', 'First Seen', 'Last Seen', 'Risk', 'Type'])
        for col in resp.json['data']:
            if col.has_key('IP'):       # Sometimes no IP is in the response
                ip = col['IP']
            else:
                ip = 'No IP'
            tdata.append([col['Domain'], col['Hostname'], ip, col['First_Seen'], col['Last_Seen'],col['Risk'], col['Type']])
            
            # Add each host to the database
            if addhosts: self.add_host(col['Hostname'], address=ip)
            
        # Print the table  
        self.table(tdata, True)
