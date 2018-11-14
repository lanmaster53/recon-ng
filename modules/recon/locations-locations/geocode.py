from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'Address Geocoder',
        'author': 'Quentin Kaiser (contact@quentinkaiser.be)',
        'description': 'Queries the Google Maps API to obtain coordinates for an address. Updates the \'locations\' table with the results.',
        'required_keys': ['google_api'],
        'query': 'SELECT DISTINCT street_address FROM locations WHERE street_address IS NOT NULL',
    }

    def module_run(self, addresses):
        api_key = self.keys.get('google_api')
        for address in addresses:
            self.verbose("Geocoding '%s'..." % (address))
            payload = {'address' : address, 'key' : api_key}
            url = 'https://maps.googleapis.com/maps/api/geocode/json'
            resp = self.request(url, payload=payload)
            # kill the module if nothing is returned
            if len(resp.json['results']) == 0:
                self.output('Unable to geocode \'%s\'.' % (address))
                return
            # loop through the results
            for result in resp.json['results']:
                lat = result['geometry']['location']['lat']
                lon = result['geometry']['location']['lng']
                # store the result
                self.add_locations(lat, lon, address)
            self.query('DELETE FROM locations WHERE street_address=? AND latitude IS NULL AND longitude IS NULL', (address,))
