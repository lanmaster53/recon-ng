import framework
# unique to module
import urllib
import re
import sys

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('handle', '@lanmaster53', 'yes', 'target twitter handle')
        self.register_option('dtg', None, 'no', 'date-time group in the form YYYY-MM-DD')
        self.info = {
                     'Name': 'Twitter Handles',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches Twitter for users that mentioned, or were mentioned by, the given handle.',
                     'Comments': [
                                  'Twitter only saves tweets for 6-8 days at this time.'
                                  ]
                     }
    def module_run(self):
        self.handle_options()
        header = ['Handle', 'Name', 'Time']
        
        self.tdata = []
        # search for mentions tweeted by the given handle
        self.output('Searching for users mentioned by the given handle.')
        self.search_handle_tweets()
        if self.tdata:
            print ''
            self.tdata.insert(0, header)
            self.table(self.tdata, header=True)

        self.tdata = []
        # search for tweets mentioning the given handle
        self.output('Searching for users who mentioned the given handle.')
        self.search_handle_mentions()
        if self.tdata:
            print ''
            self.tdata.insert(0, header)
            self.table(self.tdata, header=True)

    def handle_options(self):
        '''
        Method built to do quick and dirty parsing of options supplied by the user.
        Sets two properties of this class instance, self.handle and self.dtg.
        '''
        # handle
        handle = self.options['handle']['value']
        self.handle = handle if not handle.startswith('@') else handle[1:]
        # dtg
        dtg = self.options['dtg']['value']
        if not dtg:
            dtg = '2011-01-01'
        elif not re.match(r'\d\d\d\d-\d\d-\d\d', dtg):
            dtg = '2011-01-01'
            self.output('DTG should be in the format: YYYY-MM-DD. Using the default value of \'%s\'.' % (dtg))
        self.dtg = dtg

    def get_user_info(self, handle, time):
        '''
        Queries twitter for information on a given twitter handle.
        Twitter API returns ALOT of good info, database does not currently handle most of it.
        '''
        url = 'https://api.twitter.com/1/users/show.json'
        payload = {'screen_name': handle, 'include_entities': 'true'}
        resp = self.request(url, payload=payload)
        
        jsonobj = resp.json
        for item in ['error', 'errors']:
            if item in jsonobj:
                self.error(jsonobj[item])
                return

        name = jsonobj['name']
        if not [handle, name, time] in self.tdata: self.tdata.append([handle, name, time])

    def search_api(self, query):
        payload = {'q': query}
        url = 'http://search.twitter.com/search.json'
        resp = self.request(url, payload=payload)
        
        jsonobj = resp.json
        for item in ['error', 'errors']:
            if item in jsonobj:
                self.error(jsonobj[item])
                return

        return jsonobj

    def search_handle_tweets(self):
        '''
        Searches for mentions tweeted by the given handle.
        Pulls usernames out and sends to get_user_info.
        '''
        resp = self.search_api('from:%s since:%s' % (self.handle, self.dtg))
        if resp:
            for tweet in resp['results']:
                if 'to_user' in tweet:
                    self.get_user_info(tweet['to_user'], tweet['created_at'])

    def search_handle_mentions(self):
        '''
        Searches for tweets mentioning the given handle.
        Checks using "to:" and "@" operands in the API.
        Passes identified handles to get_user_info.
        '''
        for operand in ['to:', '@']:
            resp = self.search_api('%s%s since:%s' % (operand, self.handle, self.dtg))
            if resp:
                for tweet in resp['results']:
                    if 'to_user' in tweet:
                        self.get_user_info(tweet['from_user'], tweet['created_at'])
