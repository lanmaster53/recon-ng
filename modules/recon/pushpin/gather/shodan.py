from framework import *
# unique to module
from datetime import datetime

class Module(Framework):

    def __init__(self, params):
        Framework.__init__(self, params)
        self.register_option('latitude', self.global_options['latitude'], 'yes', self.global_options.description['latitude'])
        self.register_option('longitude', self.global_options['longitude'], 'yes', self.global_options.description['longitude'])
        self.register_option('radius', self.global_options['radius'], 'yes', 'radius in kilometers')
        self.register_option('restrict', True, 'yes', 'limit number of api requests to \'REQUESTS\'')
        self.register_option('requests', 1, 'yes', 'maximum number of api requests to make')
        self.info = {
                     'Name': 'Shodan Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Shodan for hosts in specified proximity to the given location.',
                     'Comments': [
                                  'Shodan \'geo\' searches can take a long time to complete. If receiving connection timeout errors, increase the global SOCKET_TIMEOUT option.']
                     }
    def module_run(self):
        lat = self.options['latitude']
        lon = self.options['longitude']
        rad = self.options['radius']
        query = 'geo:%f,%f,%d' % (lat, lon, rad)
        limit = self.options['requests'] if self.options['restrict'] else 0
        results = self.search_shodan_api(query, limit)
        new = 0
        for host in results:
            os = host['os'] if 'os' in host else ''
            hostname = host['hostnames'][0] if len(host['hostnames']) > 0 else 'None'
            protocol = '%s:%d' % (host['ip'], host['port'])
            source = 'Shodan'
            screen_name = protocol
            profile_name = protocol
            profile_url = 'http://%s' % (protocol)
            media_url = 'http://www.shodanhq.com/search?q=net:%s' % (host['ip'])
            thumb_url = 'data:image/png;base64,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'
            message = 'Hostname: %s | City: %s, %s | OS: %s' % (hostname, host['city'], host['country_name'], os)
            latitude = host['latitude']
            longitude = host['longitude']
            time = datetime.strptime(host['updated'], '%d.%m.%Y').strftime('%Y-%m-%d %H:%M:%S')
            new += self.add_pushpin(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
        self.output('%d total items found.' % (len(results)))
        if new: self.alert('%d NEW items found!' % (new))
