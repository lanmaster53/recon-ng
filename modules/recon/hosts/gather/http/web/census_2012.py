import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT netblock FROM netblocks WHERE netblock IS NOT NULL ORDER BY netblock')
        self.register_option('store_table', False, 'no', 'store the results in a database table')
        self.info = {
                     'Name': 'Internet Census 2012 Lookup',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Queries the Internet Census 2012 data through Exfiltrated.com to enumerate open ports for a netblock.',
                     'Comments': [
                                  'http://exfiltrated.com/querystart.php'
                                  ]
                     }
   
    def module_run(self, netblocks):
        url = 'http://exfiltrated.com/query.php'
        tdata = []
        self.output('Gathering port scan data...')
        for netblock in netblocks:
            addresses = self.cidr_to_list(netblock)
            first = addresses[0]
            last = addresses[-1]
            self.verbose('%s (%s - %s)' % (netblock, first, last))
            payload = {'startIP': first, 'endIP': last, 'includeHostnames': 'Yes', 'rawDownload': 'Yes'}
            resp = self.request(url, payload=payload)
            for host in resp.text.strip().split('\r\n')[1:]:
                address = host.split('\t')[1]
                port = host.split('\t')[2]
                hostname = host.split('\t')[0]
                tdata.append([hostname, address, port])
        if not tdata:
            self.output('No scan data available.')
            return
        header=['hostname', 'address', 'port']
        self.table(tdata, header=header, title='Census 2012', store=self.options['store_table'])
