import framework
# unique to module
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.register_option('store_table', None, 'no', 'name for a table to create in the database and store the complete result set')
        self.register_option('store_column', None, 'no', 'name for a column to create in the hosts table and store open port information')
        self.info = {
                     'Name': 'Internet Census 2012 Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the Internet Census 2012 data through Exfiltrated.com to enumerate open ports on target hosts.',
                     'Comments': [
                                  'Source options: [ <range> | <cidr> | db | <address> | ./path/to/file | query <sql> ]',
                                  'This module updates only previously harvested hosts when using the \'store_column\' option.',
                                  'http://exfiltrated.com/querystart.php'
                                  ]
                     }
   
    def module_run(self):

        # configure module input
        source = self.options['source']
        ranges = []
        if re.search('\d+\.\d+\.\d+\.\d+[\s\-/]', source):
            raw_ranges = source.split(',')
            for raw_range in raw_ranges:
                ips = raw_range.strip()
                if re.search('\d+\.\d+\.\d+\.\d+\s*-\s*\d+\.\d+\.\d+\.\d+', ips):
                    first = ips.split('-')[0].strip()
                    last = ips.split('-')[1].strip()
                    ranges.append((first, last))
                elif re.search('\d+\.\d+\.\d+\.\d+/\d+', ips):
                    ips = self.cidr_to_list(ips)
                    first = ips[0]
                    last = ips[-1]
                    ranges.append((first, last))
        else:
            addresses = self.get_source(source, 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL ORDER BY host')
            for address in addresses:
                ranges.append((address, address))

        # begin module processing
        table = self.options['store_table']
        column = self.options['store_column']
        tdata = []
        for ips in ranges:
            first = ips[0]
            last = ips[1]
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

        # manage module output
        if not tdata:
            self.output('No scan data available.')
            return
        header = ['address', 'port', 'hostname']
        self.table(tdata, header=header)

        # store data
        if table:
            try: self.add_table(table, tdata, header=header)
            except framework.FrameworkException as e:
                self.error(e.message)
        if column:
            try:
                try:
                    self.add_column('hosts', column)
                except framework.FrameworkException as e:
                    self.error(e.message)
                    self.alert('Overwriting the existing \'%s\' column.' % (column))
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
