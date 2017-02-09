from recon.core.module import BaseModule
from datetime import datetime

class Module(BaseModule):

    meta = {
        'name': 'Shodan Geolocation Search',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Searches Shodan for media in the specified proximity to a location.',
        'required_keys': ['shodan_api'],
        'comments': (
            'Shodan \'geo\' searches can take a long time to complete. If receiving connection timeout errors, increase the global SOCKET_TIMEOUT option.',
        ),
        'query': 'SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
        'options': (
            ('radius', 1, True, 'radius in kilometers'),
            ('limit', 1, True, 'limit number of api requests per input source (0 = unlimited)'),
        ),
    }

    def module_run(self, points):
        limit = self.options['limit']
        rad = self.options['radius']
        for point in points:
            self.heading(point, level=0)
            query = 'geo:%s,%d' % (point, rad)
            results = self.search_shodan_api(query, limit)
            for host in results:
                os = host['os'] if 'os' in host else ''
                hostname = host['hostnames'][0] if len(host['hostnames']) > 0 else 'None'
                protocol = '%s:%d' % (host['ip_str'], host['port'])
                source = 'Shodan'
                screen_name = protocol
                profile_name = protocol
                profile_url = 'http://%s' % (protocol)
                media_url = 'https://www.shodan.io/host/%s' % (host['ip_str'])
                thumb_url = 'https://gravatar.com/avatar/ffc4048d63729d4932fd3cc45139174f?s=300'
                message = 'Hostname: %s | City: %s, %s | OS: %s' % (hostname, host['location']['city'], host['location']['country_name'], os)
                latitude = host['location']['latitude']
                longitude = host['location']['longitude']
                time = datetime.strptime(host['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')
                self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
