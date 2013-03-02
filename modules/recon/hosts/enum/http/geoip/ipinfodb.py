import framework
# unique to module
import json

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of target IP addresses')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'IPInfoDB GeoIP',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages the ipinfodb.com API to geolocate the given host(s) by IP address and updates the \'hosts\' table of the database with the results.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]'
                                  ]
                     }
   
    def module_run(self):
        verbose = self.options['verbose']['value']
        api_key = self.manage_key('ipinfodb', 'IPInfoDB API key')
        if not api_key: return
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        if not hosts: return

        for host in hosts:
            # request the scan
            url = 'http://api.ipinfodb.com/v3/ip-city/?key=%s&ip=%s&format=json' % (api_key, host)
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
            if jsonobj['statusCode'].lower() == 'error':
                self.error(jsonobj['statusMessage'])
                continue

            if self.options['source']['value'] == 'db':
                location = []
                for name in ['cityName', 'regionName']:
                    if jsonobj[name]: location.append(str(jsonobj[name]).title())
                data = [', '.join(location)]
                data.append(jsonobj['countryName'].title())
                data.append(str(jsonobj['latitude']))
                data.append(str(jsonobj['longitude']))
                data.append(host)
                self.query('UPDATE hosts SET region=\'%s\', country=\'%s\', latitude=\'%s\', longitude=\'%s\' WHERE ip_address=\'%s\'' % tuple(data))

            tdata = [['Host Info', 'Value']]
            for key in jsonobj:
                tdata.append([key, jsonobj[key]])
            # output the results in table format
            self.table(tdata, True)
