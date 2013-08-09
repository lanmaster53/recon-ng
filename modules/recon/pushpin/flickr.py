import framework
# unique to module
import json
from datetime import datetime

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('latitude', self.goptions['latitude']['value'], 'yes', self.goptions['latitude']['desc'])
        self.register_option('longitude', self.goptions['longitude']['value'], 'yes', self.goptions['longitude']['desc'])
        self.register_option('radius', self.goptions['radius']['value'], 'yes', 'radius in kilometers')
        self.info = {
                     'Name': 'Flickr Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Flickr for media in specified proximity to the given location.',
                     'Comments': [
                                  'Radius must be greater than zero and less than 32 kilometers.'
                                  ]
                     }
    def module_run(self):
        api_key = self.get_key('flickr_api')
        lat = self.options['latitude']['value']
        lon = self.options['longitude']['value']
        rad = self.options['radius']['value']
        payload = {'method': 'flickr.photos.search', 'format': 'json', 'api_key': api_key, 'text': '-', 'lat': lat, 'lon': lon, 'has_geo': 1, 'extras': 'date_upload,date_taken,owner_name,geo,url_t,url_m', 'radius': rad, 'radius_units':'km', 'per_page': 500}
        url = 'http://api.flickr.com/services/rest/'
        cnt = 0
        new = 0
        while True:
            resp = self.request(url, payload=payload)
            jsonobj = json.loads(resp.text[14:-1])
            # check for, and exit on, an erroneous request
            if jsonobj['stat'] == 'fail':
                self.error(jsonobj['message'])
                break
            for photo in jsonobj['photos']['photo']:
                source = 'Flickr'
                screen_name = photo['owner']
                profile_name = photo['ownername']
                profile_url = 'http://flickr.com/photos/%s' % screen_name
                media_url = photo['url_m']
                thumb_url = photo['url_t']
                message = photo['title']
                latitude = photo['latitude']
                longitude = photo['longitude']
                try: time = datetime.strptime(photo['datetaken'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError: time = datetime(1970, 1, 1).strftime('%Y-%m-%d %H:%M:%S')
                new += self.add_pushpin(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                cnt += 1
            if jsonobj['photos']['page'] >= jsonobj['photos']['pages']:
                break
            payload['page'] = jsonobj['photos']['page'] + 1
        self.output('%d total items found.' % (cnt))
        if new: self.alert('%d NEW items found!' % (new))
