from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'Reverse Geocoder',
        'author': 'Quentin Kaiser (contact@quentinkaiser.be)',
        'description': 'Queries the Google Maps API to obtain an address from coordinates.',
        'required_keys': ['google_api'],
        'query': 'SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
    }

    def module_run(self, points):
        api_key = self.keys.get('google_api')
        for point in points:
            self.verbose("Reverse geocoding (%s)..." % (point))
            payload = {'latlng' : point, 'key' : api_key}
            url = 'https://maps.googleapis.com/maps/api/geocode/json'
            resp = self.request(url, payload=payload)
            # kill the module if nothing is returned
            if len(resp.json['results']) == 0:
                self.output('Unable to resolve an address for (%s).' % (point))
                return
            # loop through the results
            found = False
            for result in resp.json['results']:
                if result['geometry']['location_type'] == 'ROOFTOP':
                    found = True
                    lat = point.split(',')[0]
                    lon = point.split(',')[1]
                    address = result['formatted_address']
                    # store the result
                    self.add_locations(lat, lon, address)
            if found: self.query('DELETE FROM locations WHERE latitude=? AND longitude=? AND street_address IS NULL', (lat, lon))
