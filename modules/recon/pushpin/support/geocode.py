import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('address', None, 'yes', 'address to geocode')
        self.register_option('store', True , 'yes', 'store the obtained coordinates to latitude, longitude')
        self.info = {
            'Name': 'Address Geocoder',
            'Author': 'Quentin Kaiser (contact@quentinkaiser.be)',
            'Description': 'Call the Google Maps API to obtain coordinates from an address.',
            'Comments': []
        }

    def module_run(self):
        address = self.options['address']
        store = self.options['store']
        self.verbose("Geocoding '%s'..." % (address))
        payload = {'address' : address, 'sensor' : 'false'}
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        resp = self.request(url, payload=payload)
        # kill the module if nothing is returned
        if len(resp.json['results']) == 0:
            self.output('Unable to geocode \'%s\'.' % (address))
            return
        # loop through and output the results
        for result in resp.json['results']:
            lat = result['geometry']['location']['lat']
            lon = result['geometry']['location']['lng']
            self.alert("Latitude: %s, Longitude: %s" % (lat, lon))
        # store if True and only 1 set of coordinates is returned
        if store:
            if len(resp.json['results']) == 1:
                self.global_options['latitude']['value'] = lat
                self.global_options['longitude']['value'] = lon
                self.verbose('Global options, latitude and longitude, set.')
            elif len(resp.json['results']) > 1:
                self.output('More than 1 result returned. Global options not set.')
