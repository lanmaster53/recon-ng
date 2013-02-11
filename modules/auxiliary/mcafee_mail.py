import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'McAfee Mail Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks mcafee.com site for mail servers for given domain.',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.xssed()

    def xssed(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']

        url = 'http://www.mcafee.com/threat-intelligence/jsproxy/domain.ashx?q=mail&f=%s' % (domain)
        if verbose: self.output('URL being retrieved: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
        except Exception as e:
            self.error(e.__str__())
            return

        if resp:
            # Output the results in table format
            tdata = [] 
            tdata.append(['Domain', 'MX_Data', 'IP_Address', 'Weight'])
            for col in resp.json['data']:
                tdata.append([col['Domain'], col['MX_Data'], col['IP_Address'], col['Weight']])
                
                # Add each host to the database
                self.add_host(col['MX_Data'], address=col['IP_Address'])
                
            self.table(tdata, True)
            

        else:
            self.output('No results found')
        
