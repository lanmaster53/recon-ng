from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Twitter Mentioned',
        'author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
        'description': 'Leverages the Twitter API to enumerate users that mentioned the given handle. Updates the \'profiles\' table with the results.',
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
            for operand in ['to:', '@']:
                results = self.search_twitter_api({'q':'%s%s' % (operand, handle)}, self.options['limit'])
                for tweet in results:
                    handle = tweet['user']['screen_name']
                    name = tweet['user']['name']
                    time = tweet['created_at']
                    self.add_profiles(username=handle, resource='Twitter', url='https://twitter.com/' + handle, category='social', notes=name)
