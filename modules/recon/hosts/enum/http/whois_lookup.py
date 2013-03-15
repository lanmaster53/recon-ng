import framework
# unique to module
from urlparse import urlparse

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Whois Query',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Uses the ARIN Whois RWS to query whois data for the given IP addresses.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        addresses = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        if not addresses: return

        for address in addresses:
            url = 'http://whois.arin.net/rest/ip/%s/pft.txt' % (address)
            self.verbose('URL: %s' % url)
            try: resp = self.request(url)
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                continue
            #print resp.text.strip()
            lines = resp.text.strip().split('\n')
            tdata = []
            for line in lines:
                if line:
                    name = line.split(':', 1)[0].strip()
                    value = line.split(':', 1)[1].strip()
                    tdata.append([name.title(), value])
                elif last_line:
                    # removes extra spacing
                    tdata.append([None, None])
                last_line = line
            if tdata: self.table(tdata)
