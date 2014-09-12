import module
# unique to module
from datetime import datetime

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL')
        self.register_option('radius', 1, True, 'radius in kilometers')
        self.info = {
                     'Name': 'YouTube Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches YouTube for media in the specified proximity to a location.',
                     'Comments': [
                                  'Radius must be greater than zero and less than 1000 kilometers.'
                                  ]
                     }

    def module_run(self, points):
        #self.alert('This module is broken due to YouTube API issues. See https://code.google.com/p/gdata-issues/issues/detail?id=4234 for details.')
        #return
        rad = self.options['radius']
        url = 'http://gdata.youtube.com/feeds/api/videos'
        count = 0
        new = 0
        for point in points:
            self.heading(point, level=0)
            payload = {'alt': 'json', 'location': '%s!' % (point), 'location-radius': '%dkm' % (rad)}
            processed = 0
            while True:
                resp = self.request(url, payload=payload)
                jsonobj = resp.json
                if not jsonobj:
                    self.error(resp.text)
                    break
                if not count: self.output('Collecting data for an unknown number of videos...')
                if not 'entry' in jsonobj['feed']: break
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
                    new += self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                    count += 1
                processed += len(jsonobj['feed']['entry'])
                self.verbose('%s photos processed.' % (processed))
                qty = jsonobj['feed']['openSearch$itemsPerPage']['$t']
                start = jsonobj['feed']['openSearch$startIndex']['$t']
                next = qty + start
                if next > 500: break
                payload['start-index'] = next
        self.summarize(new, count)
