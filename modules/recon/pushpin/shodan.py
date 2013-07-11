import framework
# unique to module
from datetime import datetime

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('latitude', self.goptions['latitude']['value'], 'yes', self.goptions['latitude']['desc'])
        self.register_option('longitude', self.goptions['longitude']['value'], 'yes', self.goptions['longitude']['desc'])
        self.register_option('radius', 1, 'yes', 'radius in kilometers')
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
        lat = self.options['latitude']['value']
        lon = self.options['longitude']['value']
        rad = self.options['radius']['value']
        query = 'geo:%f,%f,%d' % (lat, lon, rad)
        limit = self.options['requests']['value'] if self.options['restrict']['value'] else 0
        results = self.search_shodan_api(query, limit)
        for host in results:
            os = host['os'] if 'os' in host else ''
            hostname = host['hostnames'][0] if len(host['hostnames']) > 0 else ''
            protocol = '%s:%d' % (host['ip'], host['port'])
            source = 'Shodan'
            screen_name = protocol
            profile_name = protocol
            profile_url = 'http://%s' % (protocol)
            media_url = 'http://www.shodanhq.com/search?q=net:%s' % (host['ip'])
            thumb_url = ''
            message = '%s<br />City: %s, %s<br />OS: %s' % (hostname, host['city'], host['country_name'], os)
            latitude = host['latitude']
            longitude = host['longitude']
            time = datetime.strptime(host['updated'], '%d.%m.%Y').strftime('%Y-%m-%d %H:%M:%S')
            self.add_pushpin(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
