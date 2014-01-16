from framework import *
# unique to module
import json

class Module(Framework):

    def __init__(self, params):
        Framework.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'HostIP GeoIP',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the hostip.info API to geolocate the given host(s) by IP address and updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')

        for host in hosts:
            # request the scan
            url = 'http://api.hostip.info/get_json.php?ip=%s&position=true' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (host, resp.text))
                continue

            if self.options['source'] == 'db':
                data = [jsonobj['city'].title()]
                data.append(jsonobj['country_name'].title())
                data.append(str(jsonobj['lat']))
                data.append(str(jsonobj['lng']))
                data.append(host)
                self.query('UPDATE hosts SET region=?, country=?, latitude=?, longitude=? WHERE ip_address=?', tuple(data))

            tdata = [['Host Info', 'Value']]
            for key in jsonobj:
                tdata.append([key, jsonobj[key]])
            # output the results in table format
            self.table(tdata, True)
