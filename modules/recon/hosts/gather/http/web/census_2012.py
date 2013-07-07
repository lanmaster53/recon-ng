import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('ip_first', None, 'yes', 'first address in the target range.')
        self.register_option('ip_last', None, 'yes', 'last address in the target range.')
        self.register_option('store', None, 'no', 'name of database table to store the results or data will not be stored.')
        self.info = {
                     'Name': 'Internet Census 2012 Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the Internet Census 2012 data through Exfiltrated.com to enumerate open ports on target hosts.',
                     'Comments': [
                                  'http://exfiltrated.com/querystart.php'
                                  ]
                     }
   
    def module_run(self):
        first = self.options['ip_first']['value']
        last = self.options['ip_last']['value']
        payload = {'startIP': first, 'endIP': last, 'includeHostnames': 'Yes', 'rawDownload': 'Yes'}
        url = 'http://exfiltrated.com/query.php'
        resp = self.request(url, payload=payload)
        tdata = []
        for host in resp.text.strip().split('\r\n'):
            tdata.append(host.split('\t'))
        self.table(tdata, header=True, table=self.options['store']['value'])
