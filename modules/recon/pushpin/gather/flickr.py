import framework
# unique to module
import json
from datetime import datetime

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('latitude', self.global_options['latitude'], 'yes', self.global_options.description['latitude'])
        self.register_option('longitude', self.global_options['longitude'], 'yes', self.global_options.description['longitude'])
        self.register_option('radius', self.global_options['radius'], 'yes', 'radius in kilometers')
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
        lat = self.options['latitude']
        lon = self.options['longitude']
        rad = self.options['radius']
        payload = {'method': 'flickr.photos.search', 'format': 'json', 'api_key': api_key, 'lat': lat, 'lon': lon, 'has_geo': 1, 'min_taken_date': '1990-01-01 00:00:00', 'extras': 'date_upload,date_taken,owner_name,geo,url_t,url_m', 'radius': rad, 'radius_units':'km', 'per_page': 500}
        url = 'http://api.flickr.com/services/rest/'
        processed = 0
        count = 0
        new = 0
        while True:
            resp = self.request(url, payload=payload)
            jsonobj = json.loads(resp.text[14:-1])
            # check for, and exit on, an erroneous request
            if jsonobj['stat'] == 'fail':
                self.error(jsonobj['message'])
                break
            if not count: self.output('Collecting data for ~%s total photos...' % (jsonobj['photos']['total']))
            for photo in jsonobj['photos']['photo']:
                latitude = photo['latitude']
                longitude = photo['longitude']
                if not all((latitude, longitude)): continue
                source = 'Flickr'
                screen_name = photo['owner']
                profile_name = photo['ownername']
                profile_url = 'http://flickr.com/photos/%s' % screen_name
                media_url = photo['url_m']
                thumb_url = photo['url_t']
                message = photo['title']
                try: time = datetime.strptime(photo['datetaken'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                except ValueError: time = datetime(1970, 1, 1).strftime('%Y-%m-%d %H:%M:%S')
                new += self.add_pushpin(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                count += 1
            processed += len(jsonobj['photos']['photo'])
            self.verbose('%s photos processed.' % (processed))
            if jsonobj['photos']['page'] >= jsonobj['photos']['pages']:
                break
            payload['page'] = jsonobj['photos']['page'] + 1
        self.output('%d total items found.' % (count))
        if new: self.alert('%d NEW items found!' % (new))
