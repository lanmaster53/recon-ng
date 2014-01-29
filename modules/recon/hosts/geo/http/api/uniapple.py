import framework
# unique to module
import json

class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Uniapple GeoIP',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the Uniapple.net API to geolocate the given host(s) by IP address and updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')

        for host in hosts:
            # request the scan
            url = 'http://uniapple.net/geoip/?ip=%s' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (host, resp.text))
                continue

            if self.options['source'] == 'db':
                location = []
                for name in ['city', 'region']:
                    if jsonobj[name]: location.append(str(jsonobj[name]))
                data = [', '.join(location)]
                data.append(jsonobj['country'].title())
                data.append(str(jsonobj['latitude']))
                data.append(str(jsonobj['longitude']))
                data.append(host)
                self.query('UPDATE hosts SET region=?, country=?, latitude=?, longitude=? WHERE ip_address=?', tuple(data))

            tdata = []
            for key in jsonobj:
                tdata.append([key, jsonobj[key]])
            # output the results in table format
            self.table(tdata, header=['Host Info', 'Value'])
