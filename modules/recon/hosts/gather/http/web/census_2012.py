import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('range', None, 'yes', 'comma delineated list of ip address ranges (no cidr).')
        self.register_option('store_table', None, 'no', 'name for a table to create in the database and store the complete result set.')
        self.register_option('store_column', None, 'no', 'name for a column to create in the hosts table and store open port information.')
        self.info = {
                     'Name': 'Internet Census 2012 Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the Internet Census 2012 data through Exfiltrated.com to enumerate open ports on target hosts.',
                     'Comments': [
                                  'This module updates only previously harvested hosts when using the \'store_column\' option.'
                                  'http://exfiltrated.com/querystart.php'
                                  ]
                     }
   
    def module_run(self):
        ranges = self.options['range']['value'].split(',')
        table = self.options['store_table']['value']
        column = self.options['store_column']['value']
        tdata = []
        cdata = []
        for ips in ranges:
            cnt = 0
            self.output('Gathering port scan data for range: %s' % (ips))
            first = ips.split('-')[0]
            last = ips.split('-')[1]
            payload = {'startIP': first, 'endIP': last, 'includeHostnames': 'Yes', 'rawDownload': 'Yes'}
            url = 'http://exfiltrated.com/query.php'
            resp = self.request(url, payload=payload)
            for host in resp.text.strip().split('\r\n')[1:]:
                address = host.split('\t')[1]
                port = host.split('\t')[2]
                cdata.append((address, port))
                hostname = host.split('\t')[0]
                tdata.append([address, port, hostname])
                cnt += 1
            if cnt: self.alert('%d entries found!' % (cnt))
        tdata.insert(0, ['address', 'port', 'hostname'])
        self.table(tdata, header=True)
        if table: self.add_table(table, tdata, header=True)
        if column: self.add_column('hosts', 'ip_address', column, cdata)
