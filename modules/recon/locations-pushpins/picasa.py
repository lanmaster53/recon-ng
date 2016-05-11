from recon.core.module import BaseModule
from datetime import datetime
import math

class Module(BaseModule):

    meta = {
        'name': 'Picasa Geolocation Search',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Searches Picasa for media in the specified proximity to a location.',
        'query': 'SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
        'options': (
            ('radius', 1, True, 'radius in kilometers'),
        ),
    }
 
    def module_run(self, points):
        rad = self.options['radius']
        url = 'http://picasaweb.google.com/data/feed/api/all'
        kilometers_per_degree_latitude = 111.12
        for point in points:
            self.heading(point, level=0)
            lat = point.split(',')[0]
            lon = point.split(',')[1]
            # http://www.johndcook.com/blog/2009/04/27/converting-miles-to-degrees-longitude-or-latitude
            west_boundary = float(lon) - (math.cos(math.radians(float(lat))) * float(rad) / kilometers_per_degree_latitude)
            south_boundary = float(lat) - (float(rad) / kilometers_per_degree_latitude)
            east_boundary = float(lon) + (math.cos(math.radians(float(lat))) * float(rad) / kilometers_per_degree_latitude)
            north_boundary = float(lat) + (float(rad) / kilometers_per_degree_latitude)
            payload = {'alt': 'json', 'strict': 'true', 'bbox': '%.6f,%.6f,%.6f,%.6f' % (west_boundary, south_boundary, east_boundary, north_boundary)}
            processed = 0
            while True:
                resp = self.request(url, payload=payload)
                jsonobj = resp.json
                if not jsonobj:
                    self.error(resp.text)
                    break
                if not processed:
                    self.output('Collecting data for an unknown number of photos...')
                if not 'entry' in jsonobj['feed']:
                    break
                for photo in jsonobj['feed']['entry']:
                    if 'georss$where' not in photo:
                        continue
                    source = 'Picasa'
                    screen_name = photo['author'][0]['name']['$t']
                    profile_name = photo['author'][0]['name']['$t']
                    profile_url = photo['author'][0]['uri']['$t']
                    media_url = photo['content']['src']
                    thumb_url = '/s72/'.join(media_url.rsplit('/', 1))
                    message = photo['title']['$t']
                    latitude = photo['georss$where']['gml$Point']['gml$pos']['$t'].split()[0]
                    longitude = photo['georss$where']['gml$Point']['gml$pos']['$t'].split()[1]
                    time = datetime.strptime(photo['published']['$t'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                processed += len(jsonobj['feed']['entry'])
                self.verbose('%s photos processed.' % (processed))
                qty = jsonobj['feed']['openSearch$itemsPerPage']['$t']
                start = jsonobj['feed']['openSearch$startIndex']['$t']
                next = qty + start
                if next > 1000:
                    break
                payload['start-index'] = next
