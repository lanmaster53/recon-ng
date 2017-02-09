from recon.core.module import BaseModule
from datetime import datetime
import json

class Module(BaseModule):

    meta = {
        'name': 'Flickr Geolocation Search',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Searches Flickr for media in the specified proximity to a location.',
        'required_keys': ['flickr_api'],
        'comments': (
            'Radius must be greater than zero and less than 32 kilometers.',
        ),
        'query': 'SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
        'options': (
            ('radius', 1, True, 'radius in kilometers'),
        ),
    }

    def module_run(self, points):
        api_key = self.keys.get('flickr_api')
        rad = self.options['radius']
        url = 'https://api.flickr.com/services/rest/'
        for point in points:
            self.heading(point, level=0)
            lat = point.split(',')[0]
            lon = point.split(',')[1]
            payload = {'method': 'flickr.photos.search', 'format': 'json', 'api_key': api_key, 'lat': lat, 'lon': lon, 'has_geo': 1, 'min_taken_date': '1990-01-01 00:00:00', 'extras': 'date_upload,date_taken,owner_name,geo,url_t,url_m', 'radius': rad, 'radius_units':'km', 'per_page': 500}
            processed = 0
            while True:
                resp = self.request(url, payload=payload)
                jsonobj = json.loads(resp.text[14:-1])
                # check for, and exit on, an erroneous request
                if jsonobj['stat'] == 'fail':
                    self.error(jsonobj['message'])
                    break
                if not processed:
                    self.output('Collecting data for ~%s total photos...' % (jsonobj['photos']['total']))
                for photo in jsonobj['photos']['photo']:
                    latitude = photo['latitude']
                    longitude = photo['longitude']
                    if not all((latitude, longitude)):
                        continue
                    source = 'Flickr'
                    screen_name = photo['owner']
                    profile_name = photo['ownername']
                    profile_url = 'http://flickr.com/photos/%s' % screen_name
                    try:
                        media_url = photo['url_m']
                    except KeyError:
                        media_url = photo['url_t'].replace('_t.', '.')
                    thumb_url = photo['url_t']
                    message = photo['title']
                    try:
                        time = datetime.strptime(photo['datetaken'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        time = datetime(1970, 1, 1)
                    self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                processed += len(jsonobj['photos']['photo'])
                self.verbose('%s photos processed.' % (processed))
                if jsonobj['photos']['page'] >= jsonobj['photos']['pages']:
                    break
                payload['page'] = jsonobj['photos']['page'] + 1
