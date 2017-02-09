from recon.core.module import BaseModule
from datetime import datetime
import json
import re

class Module(BaseModule):

    meta = {
        'name': 'Instagram Geolocation Search',
        'author': 'Nathan Malcolm (@SintheticLabs) and Tim Tomes (@LaNMaSteR53)',
        'description': 'Searches Instagram for media in the specified proximity to a location.',
        'required_keys': ['instagram_api', 'instagram_secret'],
        'comments': (
            'Radius must be greater than zero and no more than 5 kilometers (5000 meters).',
        ),
        'query': 'SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
        'options': (
            ('radius', 1, True, 'radius in kilometers'),
        ),
    }

    def get_instagram_access_token(self):
        return self.get_explicit_oauth_token(
            'instagram',
            'basic public_content',
            'https://instagram.com/oauth/authorize/',
            'https://api.instagram.com/oauth/access_token'
        )

    def module_run(self, points):
        access_token = self.get_instagram_access_token()
        rad = str(int(self.options['radius']) * 1000)
        url = 'https://api.instagram.com/v1/media/search'
        for point in points:
            self.heading(point, level=0)
            lat = point.split(',')[0]
            lon = point.split(',')[1]
            payload = {'lat': lat, 'lng': lon, 'distance': rad, 'access_token': access_token}
            processed = 0
            while True:
                resp = self.request(url, payload=payload)
                jsonobj = json.loads(resp.text)
                # check for an erroneous request
                if jsonobj['meta']['code'] != 200:
                    # check for an expired access token
                    if jsonobj['meta']['code'] == 400:
                        # renew token
                        self.delete_key('instagram_token')
                        payload['access_token'] = self.get_instagram_access_token()
                        continue
                    self.error(jsonobj['meta']['error_message'])
                    break
                if not processed:
                    self.output('Collecting data for an unknown number of photos...')
                for item in jsonobj['data']:
                    latitude = item['location']['latitude']
                    longitude = item['location']['longitude']
                    if not all((latitude, longitude)):
                        continue
                    source = 'Instagram'
                    screen_name = item['user']['username']
                    profile_name = item['user']['full_name']
                    profile_url = 'http://instagram.com/%s' % screen_name
                    media_url = item['images']['standard_resolution']['url']
                    thumb_url = item['images']['thumbnail']['url']
                    try:
                        message = item['caption']['text']
                    except:
                        message = ''
                    try:
                        time = datetime.fromtimestamp(float(item['created_time']))
                    except ValueError:
                        time = datetime(1970, 1, 1)
                    self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                processed += len(jsonobj['data'])
                self.verbose('%s photos processed.' % (processed))
                if len(jsonobj['data']) < 20:
                    self.verbose(len(jsonobj['data']))
                    break
                payload['max_timestamp'] = jsonobj['data'][19]['created_time']
