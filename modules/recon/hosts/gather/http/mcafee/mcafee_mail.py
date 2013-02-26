import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.register_option('add_to_db', False, 'no', 'Add hosts discovered to the database.')
        self.info = {
                     'Name': 'McAfee Mail Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks mcafee.com site for mail servers for given domain. This module can update the \'hosts\' table of the database with the results.',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.mcafee_mail()

    def mcafee_mail(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']
        add_hosts = self.options['add_to_db']['value']

        url = 'http://www.mcafee.com/threat-intelligence/jsproxy/domain.ashx?q=mail&f=%s' % (domain)
        if verbose: self.output('URL being retrieved: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        if not resp.json:
            self.error('Invalid JSON returned.')
            return

        # Output the results in table format
        tdata = [] 
        tdata.append(['Domain', 'MX_Data', 'IP_Address', 'Weight'])
        for col in resp.json['data']:
            tdata.append([col['Domain'], col['MX_Data'], col['IP_Address'], col['Weight']])
            
            # Add each host to the database
            if add_hosts: self.add_host(col['MX_Data'])
            
        # Print the table            
        self.table(tdata, True)
