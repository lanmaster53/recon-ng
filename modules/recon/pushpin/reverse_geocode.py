import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('latitude', self.goptions['latitude']['value'], 'yes', self.goptions['latitude']['desc'])
        self.register_option('longitude', self.goptions['longitude']['value'], 'yes', self.goptions['longitude']['desc'])
        self.info = {
            'Name': 'Reverse Geocoding with Google Geocoding API',
            'Author': 'Quentin Kaiser (contact@quentinkaiser.be)',
            'Description': 'Call the Google Geocoding API to obtain address from coordinates.',
            'Comments': []
        }
    def module_run(self):
        lat = self.options['latitude']['value']
        lon = self.options['longitude']['value']
        self.verbose("Requesting Google Maps API with coordinates (%f, %f)" % (lat, lon))
        payload = {'latlng' : '%f,%f'%(lat,lon), 'sensor' : 'false'}
        url = 'http://maps.googleapis.com/maps/api/geocode/json'
        resp = self.request(url, payload=payload)
        if 'status' not in resp.json or resp.json['status'] != 'OK':
            return None
        self.alert("Got address '%s'"%(resp.json['results'][0]['formatted_address']))