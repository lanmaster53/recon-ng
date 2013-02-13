import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.register_option('add_to_db', False, 'yes', 'add discovered hosts to the database.')
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
        add_hosts = self.options['add_to_db']['value']

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
            address = col['IP'] if col.has_key('IP') else ''
            tdata.append([col['Domain'], col['Hostname'], address, col['First_Seen'], col['Last_Seen'],col['Risk'], col['Type']])
            
            # Add each host to the database
            if add_hosts: self.add_host(col['Hostname'])
            
        # Print the table  
        self.table(tdata, True)