from recon.core.module import BaseModule
import json

class Module(BaseModule):

    meta = {
        'name': 'FreeGeoIP',
        'author': 'Gerrit Helm (G) and Tim Tomes (@LaNMaSteR53)',
        'description': 'Leverages the freegeoip.net API to geolocate a host by IP address. Updates the \'hosts\' table with the results.',
        'comments': (
            'Allows up to 10,000 queries per hour by default. Once this limit is reached, all requests will result in HTTP 403, forbidden, until the quota is cleared.',
        ),
        'query': 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL',
        'options': (
            ('serverurl', 'http://freegeoip.net', True, 'overwrite server url (e.g. for local installations)'),
        ),
    }
   
    def module_run(self, hosts):
        for host in hosts:
            url = '%s/json/%s' % (self.options['serverurl'], host)
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
