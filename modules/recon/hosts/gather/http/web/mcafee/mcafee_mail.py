import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('store', False, 'no', 'Add hosts discovered to the database.')
        self.info = {
                     'Name': 'McAfee Mail Host Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks mcafee.com site for mail servers for given domain and can update the \'hosts\' table of the database with the results if desired.',
                     'Comments': []
                     }
   
    def module_run(self):
        domain = self.options['domain']['value']
        add_hosts = self.options['store']['value']

        url = 'http://www.mcafee.com/threat-intelligence/jsproxy/domain.ashx?q=mail&f=%s' % (domain)
        self.verbose('URL: %s' % url)
        resp = self.request(url)
        if not resp.json:
            self.error('Invalid JSON response.\n%s' % (resp.text))
            return

        new = 0
        tdata = [] 
        for col in resp.json['data']:
            tdata.append([col['Domain'], col['MX_Data'], col['IP_Address'], col['Weight']])
            # add each host to the database
            if add_hosts: new += self.add_host(col['MX_Data'])
            
        # print the table
        if tdata:
            tdata.insert(0, resp.json['columns'])
            self.table(tdata, True)
        else:
            self.output('No results found.')
        if add_hosts and new: self.alert('%d NEW hosts found!' % (new))
