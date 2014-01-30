import module
# unique to module
from urlparse import urlparse

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'show info\' for options)')
        self.info = {
                     'Name': 'Whois Query',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the ARIN Whois RWS to query whois data for the given IP addresses.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        addresses = self.get_source(self.options['source'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')

        for address in addresses:
            url = 'http://whois.arin.net/rest/ip/%s/pft.txt' % (address)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            lines = resp.text.strip().split('\n')
            tdata = []
            last_line = ''
            for line in lines:
                if not line.startswith('#') and ':' in line:
                    name = line.split(':', 1)[0].strip()
                    value = line.split(':', 1)[1].strip()
                    tdata.append([name.title(), value])
                    last_line = line
                elif last_line:
                    tdata.append([None, None])
                    last_line = None
            if not any(tdata[-1]): del tdata[-1]
            if tdata: self.table(tdata)
