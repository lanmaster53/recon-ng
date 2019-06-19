from recon.core import framework
import time
import urllib.parse


class TwitterMixin(object):

    def get_twitter_oauth_token(self):
        token_name = 'twitter_token'
        token = self.get_key(token_name)
        if token:
            return token
        twitter_key = self.get_key('twitter_api')
        twitter_secret = self.get_key('twitter_secret')
        url = 'https://api.twitter.com/oauth2/token'
        auth = (twitter_key, twitter_secret)
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
        payload = {'grant_type': 'client_credentials'}
        resp = self.request('POST', url, auth=auth, headers=headers, data=payload)
        if 'errors' in resp.json():
            raise framework.FrameworkException(f"{resp.json()['errors'][0]['message']}, {resp.json()['errors'][0]['label']}")
        access_token = resp.json()['access_token']
        self.add_key(token_name, access_token)
        return access_token

    def search_twitter_api(self, payload, limit=False):
        headers = {'Authorization': f"Bearer {self.get_twitter_oauth_token()}"}
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        results = []
        while True:
            resp = self.request('GET', url, params=payload, headers=headers)
            if limit:
                # app auth rate limit for search/tweets is 450/15min
                time.sleep(2)
            jsonobj = resp.json()
            for item in ['error', 'errors']:
                if item in jsonobj:
                    raise framework.FrameworkException(jsonobj[item])
            results += jsonobj['statuses']
            if 'next_results' in jsonobj['search_metadata']:
                max_id = urllib.parse.parse_qs(jsonobj['search_metadata']['next_results'][1:])['max_id'][0]
                payload['max_id'] = max_id
                continue
            break
        return results
