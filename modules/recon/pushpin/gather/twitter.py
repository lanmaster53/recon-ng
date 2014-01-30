import framework
# unique to module
from datetime import datetime
from urlparse import parse_qs

class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)
        self.register_option('latitude', self.global_options['latitude'], 'yes', self.global_options.description['latitude'])
        self.register_option('longitude', self.global_options['longitude'], 'yes', self.global_options.description['longitude'])
        self.register_option('radius', self.global_options['radius'], 'yes', 'radius in kilometers')
        self.info = {
                     'Name': 'Twitter Geolocation Search',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Searches Twitter for media in specified proximity to the given location.',
                     'Comments': []
                     }
    def module_run(self):
        self.bearer_token = self.get_twitter_oauth_token()
        lat = self.options['latitude']
        lon = self.options['longitude']
        rad = self.options['radius']
        headers = {'Authorization': 'Bearer %s' % (self.bearer_token)}
        payload = {'geocode': '%f,%f,%dkm' % (lat,lon,rad), 'count': 100}
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        processed = 0
        count = 0
        new = 0
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
                new += self.add_pushpin(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                count += 1
            processed += len(jsonobj['statuses'])
            self.verbose('%s tweets processed.' % (processed))
            if 'next_results' in jsonobj['search_metadata']:
                max_id = parse_qs(jsonobj['search_metadata']['next_results'][1:])['max_id'][0]
                payload['max_id'] = max_id
                continue
            break
        self.output('%d total items found.' % (count))
        if new: self.alert('%d NEW items found!' % (new))
