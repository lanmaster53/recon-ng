import framework
# unique to module
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of target IP addresses')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Maxmind GeoIP',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Leverages maxmind.com to geolocate the given host(s) by IP address. This module updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  'Note: maxmind.com allows a maximum of 25 queries per day per source IP address.'
                                  ]
                     }
   
    def module_run(self):
        verbose = self.options['verbose']['value']

        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        if not hosts: return

        for host in hosts:
            # request the scan
            url = 'http://www.maxmind.com/geoip/city_isp_org/%s?demo=1' % (host)
            if verbose: self.output('URL: %s' % url)
            try: resp = self.request(url)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                continue

            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON returned for \'%s\'.' % (host))
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
