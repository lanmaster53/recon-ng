import framework
# unique to module
import math
from datetime import datetime

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('latitude', self.global_options['latitude']['value'], 'yes', self.global_options['latitude']['desc'])
        self.register_option('longitude', self.global_options['longitude']['value'], 'yes', self.global_options['longitude']['desc'])
        self.register_option('radius', self.global_options['radius']['value'], 'yes', 'radius in kilometers')
        self.info = {
                     'Name': 'Picasa Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Picasa for media in specified proximity to the given location.',
                     'Comments': []
                     }
    def module_run(self):
        lat = self.options['latitude']
        lon = self.options['longitude']
        rad = self.options['radius']
        kilometers_per_degree_latitude = 111.12
        # http://www.johndcook.com/blog/2009/04/27/converting-miles-to-degrees-longitude-or-latitude
        west_boundary = float(lon) - (math.cos(math.radians(float(lat))) * float(rad) / kilometers_per_degree_latitude)
        south_boundary = float(lat) - (float(rad) / kilometers_per_degree_latitude)
        east_boundary = float(lon) + (math.cos(math.radians(float(lat))) * float(rad) / kilometers_per_degree_latitude)
        north_boundary = float(lat) + (float(rad) / kilometers_per_degree_latitude)
        payload = {'alt': 'json', 'strict': 'true', 'bbox': '%.6f,%.6f,%.6f,%.6f' % (west_boundary, south_boundary, east_boundary, north_boundary)}
        url = 'http://picasaweb.google.com/data/feed/api/all'
        processed = 0
        count = 0
        new = 0
        while True:
            resp = self.request(url, payload=payload)
            jsonobj = resp.json
            if not jsonobj:
                self.error(resp.text)
                break
            if not count: self.output('Collecting data for an unknown number of photos...')
            if not 'entry' in jsonobj['feed']: break
            for photo in jsonobj['feed']['entry']:
                if not 'georss$where' in photo:
                    continue
                source = 'Picasa'
                screen_name = photo['author'][0]['name']['$t']
                profile_name = photo['author'][0]['name']['$t']
                profile_url = photo['author'][0]['uri']['$t']
                #media_url = photo['media$group']['media$content'][0]['url']
                media_url = photo['content']['src']
                thumb_url = '/s72/'.join(media_url.rsplit('/', 1))
                message = photo['title']['$t']
                latitude = photo['georss$where']['gml$Point']['gml$pos']['$t'].split()[0]
                longitude = photo['georss$where']['gml$Point']['gml$pos']['$t'].split()[1]
                time = datetime.strptime(photo['published']['$t'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
                new += self.add_pushpin(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                count += 1
            processed += len(jsonobj['feed']['entry'])
            self.verbose('%s photos processed.' % (processed))
            qty = jsonobj['feed']['openSearch$itemsPerPage']['$t']
            next = qty + jsonobj['feed']['openSearch$startIndex']['$t']
            if next > 1000: break
            payload['start-index'] = next
        self.output('%d total items found.' % (count))
        if new: self.alert('%d NEW items found!' % (new))
