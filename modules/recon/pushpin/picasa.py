import framework
# unique to module
import math
from datetime import datetime

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('latitude', self.goptions['latitude']['value'], 'yes', self.goptions['latitude']['desc'])
        self.register_option('longitude', self.goptions['longitude']['value'], 'yes', self.goptions['longitude']['desc'])
        self.register_option('radius', self.goptions['radius']['value'], 'yes', 'radius in kilometers')
        self.info = {
                     'Name': 'Picasa Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Picasa for media in specified proximity to the given location.',
                     'Comments': []
                     }
    def module_run(self):
        lat = self.options['latitude']['value']
        lon = self.options['longitude']['value']
        rad = self.options['radius']['value']
        kilometers_per_degree_latitude = 111.12
        # http://www.johndcook.com/blog/2009/04/27/converting-miles-to-degrees-longitude-or-latitude
        west_boundary = float(lon) - (math.cos(math.radians(float(lat))) * float(rad) / kilometers_per_degree_latitude)
        south_boundary = float(lat) - (float(rad) / kilometers_per_degree_latitude)
        east_boundary = float(lon) + (math.cos(math.radians(float(lat))) * float(rad) / kilometers_per_degree_latitude)
        north_boundary = float(lat) + (float(rad) / kilometers_per_degree_latitude)
        payload = {'alt': 'json', 'bbox': '%.6f,%.6f,%.6f,%.6f' % (west_boundary, south_boundary, east_boundary, north_boundary)}
        url = 'http://picasaweb.google.com/data/feed/api/all'
        cnt = 0
        new = 0
        page = 1
        while True:
            resp = self.request(url, payload=payload)
            jsonobj = resp.json
            if not jsonobj:
                self.error(resp.text)
                break
            if jsonobj['feed']['openSearch$totalResults']['$t'] == 0:
                break
            for photo in jsonobj['feed']['entry']:
                if not photo['georss$where']:
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
                cnt += 1
            qty = jsonobj['feed']['openSearch$itemsPerPage']['$t']
            start = jsonobj['feed']['openSearch$startIndex']['$t']
            next = qty + start
            total = jsonobj['feed']['openSearch$totalResults']['$t']
            if next > total:
                break
            page += 1
            payload['start-index'] = next
        self.output('%d total items found.' % (cnt))
        if new: self.alert('%d NEW items found!' % (new))
