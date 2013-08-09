import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('range', None, 'yes', 'comma delineated list of ip address ranges (no cidr).')
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
        ranges = self.options['range']['value'].split(',')
        tdata = []
        for ips in ranges:
            cnt = 0
            self.output('Gathering port scan data for range: %s' % (ips))
            first = ips.split('-')[0]
            last = ips.split('-')[1]
            payload = {'startIP': first, 'endIP': last, 'includeHostnames': 'Yes', 'rawDownload': 'Yes'}
            url = 'http://exfiltrated.com/query.php'
            resp = self.request(url, payload=payload)
            for host in resp.text.strip().split('\r\n')[1:]:
                tdata.append(host.split('\t'))
                cnt += 1
            if cnt: self.alert('%d entries found!' % (cnt))
        tdata.insert(0, ['hostname', 'address', 'port'])
        self.table(tdata, header=True, table=self.options['store']['value'])
