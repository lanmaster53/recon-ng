import module
# unique to module
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('handle', '@lanmaster53', 'yes', 'target twitter handle')
        self.register_option('until', None, 'no', 'date-time group in the form YYYY-MM-DD')
        self.info = {
                     'Name': 'Twitter Handles',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches Twitter for users that mentioned, or were mentioned by, the given handle.',
                     'Comments': [
                                  'Twitter limits searchable tweet history to ~3 days.'
                                  ]
                     }

    def module_run(self):
        self.handle_options()
        header = ['Handle', 'Name', 'Time']
        # search for mentions tweeted by the given handle
        self.output('Searching for users mentioned by the given handle...')
        tdata = self.search_handle_tweets()
        if tdata: self.table(tdata, header=header, store=False)
        # search for tweets mentioning the given handle
        self.output('Searching for users who mentioned the given handle...')
        tdata = self.search_handle_mentions()
        if tdata: self.table(tdata, header=header, store=False)

    def handle_options(self):
        '''Method built to do quick and dirty parsing of options supplied by the user.
        Sets two properties of this class instance, self.handle and self.dtg.'''
        # handle
        handle = self.options['handle']
        self.handle = handle if not handle.startswith('@') else handle[1:]
        # dtg
        dtg = self.options['until']
        if not dtg:
            dtg = '2020-01-01'
        elif not re.match(r'\d{4}-\d{2}-\d{2}', dtg):
            dtg = '2020-01-01'
            self.output('DTG should be in the format: YYYY-MM-DD. Using the default value of \'%s\'.' % (dtg))
        self.dtg = dtg

    def search_handle_tweets(self):
        '''Searches for mentions tweeted by the given handle.'''
        tdata = []
        results = self.search_twitter_api({'q':'from:%s' % (self.handle), 'until':self.dtg})
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

    def search_handle_mentions(self):
        '''Searches for tweets mentioning the given handle.
        Checks using "to:" and "@" operands in the API.'''
        tdata = []
        for operand in ['to:', '@']:
            results = self.search_twitter_api({'q':'%s%s' % (operand, self.handle), 'until':self.dtg})
            if results:
                for tweet in results:
                    handle = tweet['user']['screen_name']
                    name = tweet['user']['name']
                    time = tweet['created_at']
                    if not [handle, name, time] in tdata: tdata.append([handle, name, time])
        return tdata
