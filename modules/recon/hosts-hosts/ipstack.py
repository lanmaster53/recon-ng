from recon.core.module import BaseModule
import json

class Module(BaseModule):

    meta = {
        'name': 'ipstack',
        'author': 'Siarhei Harbachou (Tech.Insiders), Gerrit Helm (G) and Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages the ipstack.com API to geolocate a host by IP address. Updates the \'hosts\' table with the results.',
        'required_keys': ['ipstack_api'],
        'query': 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL',
    }

    def module_run(self, hosts):
        for host in hosts:
            api_key = self.keys.get('ipstack_api')
            url = 'http://api.ipstack.com/%s?access_key=%s' % (host, api_key)
            resp = self.request(url)
            if resp.json:
                jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (host, resp.text))
                continue
            region = ', '.join([str(jsonobj[x]).title() for x in ['city', 'region_name'] if jsonobj[x]]) or None
            country = jsonobj['country_name'].title()
            latitude = str(jsonobj['latitude'])
            longitude = str(jsonobj['longitude'])
            self.output('%s - %s,%s - %s' % (host, latitude, longitude, ', '.join([x for x in [region, country] if x])))
            self.query('UPDATE hosts SET region=?, country=?, latitude=?, longitude=? WHERE ip_address=?', (region, country, latitude, longitude, host))
