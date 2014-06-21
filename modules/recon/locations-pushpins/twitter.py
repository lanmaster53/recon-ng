import module
# unique to module
from datetime import datetime
from urlparse import parse_qs

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL')
        self.register_option('radius', 1, 'yes', 'radius in kilometers')
        self.info = {
                     'Name': 'Twitter Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Twitter for media in the specified proximity to a location.',
                     }

    def module_run(self, points):
        self.bearer_token = self.get_twitter_oauth_token()
        headers = {'Authorization': 'Bearer %s' % (self.bearer_token)}
        rad = self.options['radius']
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        count = 0
        new = 0
        for point in points:
            self.heading(point, level=0)
            payload = {'geocode': '%s,%dkm' % (point, rad), 'count': 100}
            processed = 0
            while True:
                resp = self.request(url, payload=payload, headers=headers)
                jsonobj = resp.json
                # check for, and exit on, an erroneous request
                for item in ['error', 'errors']:
                    if item in jsonobj:
                        self.error(jsonobj[item])
                        break
                if not count: self.output('Collecting data for an unknown number of tweets...')
                for tweet in jsonobj['statuses']:
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
                    time = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y').strftime('%Y-%m-%d %H:%M:%S')
                    new += self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                    count += 1
                processed += len(jsonobj['statuses'])
                self.verbose('%s tweets processed.' % (processed))
                if 'next_results' in jsonobj['search_metadata']:
                    max_id = parse_qs(jsonobj['search_metadata']['next_results'][1:])['max_id'][0]
                    payload['max_id'] = max_id
                    continue
                break
        self.summarize(new, count)
