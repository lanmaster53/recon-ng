from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Twitter Mentions',
        'author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
        'description': 'Leverages the Twitter API to enumerate users that were mentioned by the given handle. Updates the \'profiles\' table with the results.',
        'required_keys': ['twitter_api', 'twitter_secret'],
        'comments': (
            'Twitter limits searchable tweet history to 7 days.',
        ),
        'query': "SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL AND resource LIKE 'Twitter' COLLATE NOCASE",
        'options': (
            ('limit', True, True, 'toggle rate limiting'),
        ),
    }

    def module_run(self, handles):
        for handle in handles:
            handle = handle if not handle.startswith('@') else handle[1:]
            self.heading(handle, level=0)
            results = self.search_twitter_api({'q':'from:%s' % (handle)}, self.options['limit'])
            for tweet in results:
                if 'entities' in tweet:
                    if 'user_mentions' in tweet['entities']:
                        for mention in tweet['entities']['user_mentions']:
                            handle = mention['screen_name']
                            name = mention['name']
                            time = tweet['created_at']
                            self.add_profiles(username=handle, resource='Twitter', url='https://twitter.com/' + handle, category='social', notes=name)
