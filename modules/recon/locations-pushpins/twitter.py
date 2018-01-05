from recon.core.module import BaseModule
from datetime import datetime
from urlparse import parse_qs

class Module(BaseModule):

    meta = {
        'name': 'Twitter Geolocation Search',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Searches Twitter for media in the specified proximity to a location.',
        'required_keys': ['twitter_api', 'twitter_secret'],
        'query': 'SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
        'options': (
            ('radius', 1, True, 'radius in kilometers'),
        ),
    }

    def module_run(self, points):
        rad = self.options['radius']
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        for point in points:
            self.heading(point, level=0)
            self.output('Collecting data for an unknown number of tweets...')
            results = self.search_twitter_api({'q':'', 'geocode': '%s,%fkm' % (point, rad), 'count':'100'})
            for tweet in results:
                if not tweet['geo']:
                    continue
                tweet_id = tweet['id_str']
                source = 'Twitter'
                screen_name = tweet['user']['screen_name']
                profile_name = tweet['user']['name']
                profile_url = 'https://twitter.com/%s' % screen_name
                media_url = 'https://twitter.com/%s/statuses/%s' % (screen_name, tweet_id)
                thumb_url = tweet['user']['profile_image_url_https']
                message = tweet['text']
                latitude = tweet['geo']['coordinates'][0]
                longitude = tweet['geo']['coordinates'][1]
                time = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
                self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
            self.verbose('%s tweets processed.' % (len(results)))
