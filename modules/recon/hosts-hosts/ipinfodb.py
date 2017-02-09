from recon.core.module import BaseModule
import json
import time

class Module(BaseModule):

    meta = {
        'name': 'IPInfoDB GeoIP',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages the ipinfodb.com API to geolocate a host by IP address. Updates the \'hosts\' table with the results.',
        'required_keys': ['ipinfodb_api'],
        'query': 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL',
    }
   
    def module_run(self, hosts):
        api_key = self.keys.get('ipinfodb_api')
        for host in hosts:
            url = 'http://api.ipinfodb.com/v3/ip-city/?key=%s&ip=%s&format=json' % (api_key, host)
            resp = self.request(url)
            if resp.json:
                jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (host, resp.text))
                continue
            if jsonobj['statusCode'].lower() == 'error':
                self.error(jsonobj['statusMessage'])
                continue
            time.sleep(.7)
            region = ', '.join([str(jsonobj[x]).title() for x in ['cityName', 'regionName'] if jsonobj[x]]) or None
            country = jsonobj['countryName'].title()
            latitude = str(jsonobj['latitude'])
            longitude = str(jsonobj['longitude'])
            self.output('%s - %s,%s - %s' % (host, latitude, longitude, ', '.join([x for x in [region, country] if x])))
            self.query('UPDATE hosts SET region=?, country=?, latitude=?, longitude=? WHERE ip_address=?', (region, country, latitude, longitude, host))
