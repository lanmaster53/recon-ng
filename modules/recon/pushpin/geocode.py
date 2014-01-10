import framework
# unique to module
import __builtin__

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('address', None, 'yes', 'The address to be geocoded.')
        self.register_option('save', True , 'yes', 'Save the obtained coordinates to latitude, longitude')
        self.info = {
            'Name': 'Geocoding with Google Geocoding API',
            'Author': 'Quentin Kaiser (contact@quentinkaiser.be)',
            'Description': 'Call the Google Geocoding API to obtain coordinates from an address.',
            'Comments': []
        }
    def module_run(self):
        address = self.options['address']['value']
        save = self.options['save']['value']
        self.verbose("Requesting Google Maps API for '%s' geolocation" % (address))
        payload = {'address' : address, 'sensor' : 'false'}
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        resp = self.request(url, payload=payload)

        if 'status' not in resp.json or resp.json['status'] != 'OK':
            return None
        lat = resp.json['results'][0]['geometry']['location']['lat']
        lon = resp.json['results'][0]['geometry']['location']['lng']
        self.alert("Got geolocation ! (%s, %s)"%(lat, lon))
        if save:
            __builtin__.goptions['latitude']['value'] = lat
            __builtin__.goptions['longitude']['value'] = lon