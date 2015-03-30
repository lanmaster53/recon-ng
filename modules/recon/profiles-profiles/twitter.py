from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Twitter Handles',
        'author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
        'description': 'Searches Twitter for users that mentioned, or were mentioned by, the given handle.',
        'comments': (
            'Twitter limits searchable tweet history to ~3 days.',
        ),
        'query': 'SELECT DISTINCT username FROM profiles WHERE username IS NOT NULL AND resource=\'Twitter\' COLLATE NOCASE',
        'options': (
            ('until', None, False, 'date-time group in the form YYYY-MM-DD'),
        ),
    }

    def module_run(self, handles):
        until = self.set_until()
        header = ['Handle', 'Name', 'Time']
        for handle in handles:
            handle = handle if not handle.startswith('@') else handle[1:]
            # search for mentions tweeted by the given handle
            self.output('Searching for users mentioned by %s...' % (handle))
            tdata = self.search_handle_tweets(handle, until)
            if tdata: self.table(tdata, header=header)
            # search for tweets mentioning the given handle
            self.output('Searching for users who mentioned %s...' % (handle))
            tdata = self.search_handle_mentions(handle, until)
            if tdata: self.table(tdata, header=header)

    def set_until(self):
        dtg = self.options['until']
        if not dtg:
            dtg = '2020-01-01'
        elif not re.match(r'\d{4}-\d{2}-\d{2}', dtg):
            dtg = '2020-01-01'
            self.output('DTG should be in the format: YYYY-MM-DD. Using the default value of \'%s\'.' % (dtg))
        return dtg

    def search_handle_tweets(self, handle, until):
        '''Searches for mentions tweeted by the given handle.'''
        tdata = []
        results = self.search_twitter_api({'q':'from:%s' % (handle), 'until':until})
        if results:
            for tweet in results:
                if 'entities' in tweet:
                    if 'user_mentions' in tweet['entities']:
                        for mention in tweet['entities']['user_mentions']:
                            handle = mention['screen_name']
                            name = mention['name']
                            time = tweet['created_at']
                            if not [handle, name, time] in tdata: tdata.append([handle, name, time])
        return tdata

    def search_handle_mentions(self, handle, until):
        '''Searches for tweets mentioning the given handle.
        Checks using "to:" and "@" operands in the API.'''
        tdata = []
        for operand in ['to:', '@']:
            results = self.search_twitter_api({'q':'%s%s' % (operand, handle), 'until':until})
            if results:
                for tweet in results:
                    handle = tweet['user']['screen_name']
                    name = tweet['user']['name']
                    time = tweet['created_at']
                    if not [handle, name, time] in tdata: tdata.append([handle, name, time])
        return tdata
