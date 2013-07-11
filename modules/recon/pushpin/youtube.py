import framework
# unique to module
from datetime import datetime

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('latitude', self.goptions['latitude']['value'], 'yes', self.goptions['latitude']['desc'])
        self.register_option('longitude', self.goptions['longitude']['value'], 'yes', self.goptions['longitude']['desc'])
        self.register_option('radius', 1, 'yes', 'radius in kilometers')
        self.info = {
                     'Name': 'YouTube Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches YouTube for media in specified proximity to the given location.',
                     'Comments': [
                                  'Radius must be greater than zero and less than 1000 kilometers.'
                                  ]
                     }
    def module_run(self):
        self.alert('This module is broken due to YouTube API issues. See https://code.google.com/p/gdata-issues/issues/detail?id=4234 for details.')
        return
        lat = self.options['latitude']['value']
        lon = self.options['longitude']['value']
        rad = self.options['radius']['value']
        payload = {'alt': 'json', 'location': '%f,%f!' % (lat, lon), 'location-radius': '%dkm' % (rad)}
        url = 'http://gdata.youtube.com/feeds/api/videos'
        page = 1
        while True:
            resp = self.request(url, payload=payload)
            jsonobj = resp.json
            if jsonobj['feed']['openSearch$totalResults']['$t'] == 0:
                break
            for video in jsonobj['feed']['entry']:
                if not video['georss$where']:
                    continue
                source = 'YouTube'
                screen_name = video['author'][0]['name']['$t']
                profile_name = video['author'][0]['name']['$t']
                profile_url = 'http://www.youtube.com/user/%s' % video['author'][0]['uri']['$t'].split('/')[-1]
                media_url = video['link'][0]['href']
                thumb_url = video['media$group']['media$thumbnail'][0]['url']
                message = video['title']['$t']
                latitude = video['georss$where']['gml$Point']['gml$pos']['$t'].split()[0]
                longitude = video['georss$where']['gml$Point']['gml$pos']['$t'].split()[1]
                time = datetime.strptime(video['published']['$t'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%d %H:%M:%S')
                self.add_pushpin(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
            qty = jsonobj['feed']['openSearch$itemsPerPage']['$t']
            start = jsonobj['feed']['openSearch$startIndex']['$t']
            next = qty + start
            total = jsonobj['feed']['openSearch$totalResults']['$t']
            if next > total:
                break
            page += 1
            payload['start-index'] = next
