import framework
# unique to module
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Maxmind GeoIP',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Leverages the Maxmind.com Demo API to geolocate the given host(s) by IP address and updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  'Note: maxmind.com allows a maximum of 25 queries per day per source IP address.'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')

        for host in hosts:
            # request the scan
            url = 'http://www.maxmind.com/geoip/city_isp_org/%s?demo=1' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (host, resp.text))
                continue

            if resp.status_code != 200:
                self.error(jsonobj['error'])
            else:
                if self.options['source']['value'] == 'db':
                    location = []
                    for name in ['city', 'region_name']:
                        if jsonobj[name]: location.append(str(jsonobj[name]).title())
                    data = [', '.join(location)]
                    data.append(jsonobj['country_name'].title())
                    data.append(str(jsonobj['latitude']))
                    data.append(str(jsonobj['longitude']))
                    data.append(host)
                    self.query('UPDATE hosts SET region=\'%s\', country=\'%s\', latitude=\'%s\', longitude=\'%s\' WHERE ip_address=\'%s\'' % tuple(data))

                tdata = [['Host Info', 'Value']]
                for key in jsonobj:
                    tdata.append([key, jsonobj[key]])
                # output the results in table format
                self.table(tdata, True)
