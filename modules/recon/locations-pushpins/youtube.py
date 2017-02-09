from recon.core.module import BaseModule
from datetime import datetime

class Module(BaseModule):

    meta = {
        'name': 'YouTube Geolocation Search',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Searches the YouTube API for media in the specified proximity to a location.',
        'required_keys': ['google_api'],
        'query': 'SELECT DISTINCT latitude || \',\' || longitude FROM locations WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
        'options': (
            ('radius', 1, True, 'radius in kilometers'),
        ),
    }

    def module_run(self, locations):
        self.api_key = self.keys.get('google_api')
        self.url = 'https://www.googleapis.com/youtube/v3/%s'
        payload = {'part': 'snippet', 'type': 'video', 'key': self.api_key, 'locationRadius': '%skm' % (self.options['radius']), 'maxResults': 5}
        for location in locations:
            self.heading(location, level=0)
            payload['location'] = location
            processed = 0
            while True:
                resp = self.request(self.url % 'search', payload=payload)
                if not processed:
                    self.output('Collecting data for %d videos...' % (resp.json['pageInfo']['totalResults']))
                if not 'items' in resp.json:
                    break
                for video in resp.json['items']:
                    source = 'YouTube'
                    screen_name = video['snippet']['channelTitle'] or 'Unknown'
                    profile_name = screen_name
                    profile_url = 'http://www.youtube.com/channel/%s' % video['snippet']['channelId']
                    media_url = 'https://www.youtube.com/watch?v=%s' % video['id']['videoId']
                    thumb_url = video['snippet']['thumbnails']['high']['url']
                    message = video['snippet']['title']
                    latitude, longitude = self.get_video_geo(video['id']['videoId'])
                    time = datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
                    self.add_pushpins(source, screen_name, profile_name, profile_url, media_url, thumb_url, message, latitude, longitude, time)
                processed += len(resp.json['items'])
                self.verbose('%s videos processed.' % (processed))
                if 'nextPageToken' in resp.json:
                    payload['pageToken'] = resp.json['nextPageToken']
                    continue
                break

    def get_video_geo(self, vid):
        payload = {'part': 'recordingDetails', 'id': vid, 'key': self.api_key}
        resp = self.request(self.url % 'videos', payload=payload)
        latitude = resp.json['items'][0]['recordingDetails']['location']['latitude']
        longitude = resp.json['items'][0]['recordingDetails']['location']['longitude']
        return latitude, longitude
