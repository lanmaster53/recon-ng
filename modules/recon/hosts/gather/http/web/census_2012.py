import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('range', None, 'yes', 'comma delineated list of ip address ranges (X.X.X.X-Y.Y.Y.Y).')
        self.register_option('store_table', None, 'no', 'name for a table to create in the database and store the complete result set.')
        self.register_option('store_column', None, 'no', 'name for a column to create in the hosts table and store open port information.')
        self.info = {
                     'Name': 'Internet Census 2012 Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the Internet Census 2012 data through Exfiltrated.com to enumerate open ports on target hosts.',
                     'Comments': [
                                  'This module updates only previously harvested hosts when using the \'store_column\' option.',
                                  'http://exfiltrated.com/querystart.php'
                                  ]
                     }
   
    def module_run(self):
        ranges = self.options['range']['value'].split(',')
        table = self.options['store_table']['value']
        column = self.options['store_column']['value']
        tdata = []
        for ips in ranges:
            ips = ips.strip()
            if '/' in ips:
                ips = self.cidr_to_list(ips)
                first = ips[0]
                last = ips[-1]
            else:
                first = ips.split('-')[0].strip()
                last = ips.split('-')[1].strip()
            cnt = 0
            self.output('Gathering port scan data for range: %s - %s' % (first, last))
            payload = {'startIP': first, 'endIP': last, 'includeHostnames': 'Yes', 'rawDownload': 'Yes'}
            url = 'http://exfiltrated.com/query.php'
            resp = self.request(url, payload=payload)
            for host in resp.text.strip().split('\r\n')[1:]:
                address = host.split('\t')[1]
                port = host.split('\t')[2]
                hostname = host.split('\t')[0]
                tdata.append([address, port, hostname])
                cnt += 1
            if cnt: self.alert('%d entries found!' % (cnt))
        tdata.insert(0, ['address', 'port', 'hostname'])
        self.table(tdata, header=True)

        # store data
        if table:
            try: self.add_table(table, tdata, header=True)
            except framework.FrameworkException as e:
                self.error(e.message)
        if column:
            try:
                self.add_column('hosts', column)
                # combine the port data from duplicate addresses
                rdata = {}
                for item in tdata[1:]:
                    if item[0] not in rdata:
                        rdata[item[0]] = []
                    rdata[item[0]].append(item[1])
                for item in rdata:
                    self.query('UPDATE hosts SET "%s"=? WHERE ip_address=?' % (column), (','.join(rdata[item]), item))
            except framework.FrameworkException as e:
                self.error(e.message)
