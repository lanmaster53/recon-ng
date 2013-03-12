import framework
import urllib, re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.register_option('target', 'demo', 'yes', 'Twitter handle to target.')
        self.register_option('dtg', '2011-01-01', 'no', 'Date Time Group, in the form YYYY-MM-DD')
        self.info = {
                     'Name': 'Twitter Handles',
                     'Author': 'Robert Frost (@frosty_1313, frosty[at]unluckyfrosty.net)',
                     'Description': 'Searches Twitter for recent users that contact or were contacted by a given handle.',
                     'Comments': [
                                  'Twitter only saves tweets for 6-8 days at this time.'
                                  ]
                     }
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin module code here ===
        opts = self.handle_options()

        #Search for tweets sent by target
        self.alert('Searching for users your target sent messages to.')
        self.search_target_tweets(opts)

        #Search for tweets sent to target
        self.alert('Searching for users who sent messages to your target.')
        self.search_target_mentions(opts)

    def handle_options(self):
        ''' Handle_options
        Method built to do quick and dirty parsing of options supplied by user.
        returns two-tuple of handle and dtg'''
        handle = self.options['target']['value']
        handle = handle if handle[0] != '@' else handle[1:]
        
        dtg_re = re.compile('\d\d\d\d-\d\d-\d\d')
        dtg = self.options['dtg']['value']
        if not dtg_re.match(dtg):
            self.error('DTG should be in format YYYY-MM-DD.  Using default value instead.')
            dtg = '2011-01-01'
        return (handle, dtg)

    def get_user_info(self, handle):
        ''' get_user_info
        Queries twitter for information on a given twitter handle
        Twitter API returns ALOT of good info, database does not currently handle most of it.
        Updates contact table with information found.'''

        url = 'https://api.twitter.com/1/users/show.json'
        payload = {'screen_name': handle, 'include_entities': 'true'}
        
        try:
            resp = self.request(url, method = 'GET', payload = payload).json
        except KeyboardInterrupt:
            self.error('Interrupted during search...')
            return False
        except Exception as e:
            self.error( str(e) )
            return False
        
        if 'error' in resp:
            self.error( 'Something went wrong, Twitter returned an error.  If the issue persists, please contact the author.')
            return

        name = resp['name']
        location = resp['location']
        
        try:
            fname = name.split(' ')[0]
            lname = name.split(' ')[1]
            self.add_contact(fname, lname, handle)
            if self.options['verbose']['value']:
                print 'Adding %s %s (handle: @%s) to the contacts list.' % (fname, lname, handle)

        except:
            self.add_contact('NONE', name, handle)
    
    def search_api(self, query):
        payload = {'q': query}
        url = 'http://search.twitter.com/search.json'
        
        try:
            resp = self.request(url, method= 'GET', payload = payload).json
        except KeyboardInterrupt:
            self.error('Interrupted during search...')
            return False
        except Exception as e:
            self.error( str(e) )
            return False
        
        if 'error' in resp:
            self.error( 'Something went wrong, Twitter returned an error.  Please check your target handle.  If the issue persists, please contact the author.' )
            return False

        return resp

    def search_target_tweets(self, opts):
        ''' Search_target_tweets
        Searches for tweets your target has sent
        Pulls usernames out and sends to get_user_info.'''
        resp = self.search_api('from:%s since:%s' % (opts[0], opts[1]) )
        if resp:
            for tweet in resp['results']:
                if 'to_user' in tweet: 
                    self.get_user_info(tweet['to_user'])
        return

    def search_target_mentions(self, opts):
        ''' Search_target_mentions
        Searches Twitter two different ways for target mentions
        Checks using from: and @ operands in the API
        Passes found usernames to get_user_info.'''

        #Using to: operand
        resp = self.search_api('to:%s since:%s' %(opts[0], opts[1]) )
        if resp:
            for tweet in resp['results']:
                if 'to_user' in tweet:
                    self.get_user_info(tweet['from_user'])

        #Using @operand
        resp = self.search_api('@%s since:%s' %(opts[0], opts[1]) )
        if resp:
            for tweet in resp['results']:
                if 'to_user' in tweet:
                    self.get_user_info(tweet['from_user'])
