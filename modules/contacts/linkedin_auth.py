import _cmd
import __builtin__
# unique to module
import oauth2 as oauth
import httplib2
import urlparse
import webbrowser
import sys
import urllib
import json
import re

class Module(_cmd.base_cmd):

    def __init__(self, params):
        _cmd.base_cmd.__init__(self, params)
        self.options = {
                        'company': self.goptions['company'],
                        'keywords': '',
                        'verbose': False
                        }

    def do_info(self, params):
        print ''
        print 'Harvests contacts from Jigsaw.com.'
        print ''

    def do_run(self, params):
        consumer_key = self.manage_key('linkedin_key', 'LinkedIn API Key')
        if not consumer_key: return
        consumer_secret = self.manage_key('linkedin_secret', 'LinkedIn Secret Key') 
        if not consumer_secret: return
        # Use API key and secret to instantiate consumer object
        self.consumer = oauth.Consumer(consumer_key, consumer_secret)
        self.access_token = {'oauth_token': self.get_key_from_file('linkedin_token'),'oauth_token_secret': self.get_key_from_file('linkedin_token_secret')}
        if not self.access_token['oauth_token']: self.get_access_tokens()
        if self.access_token['oauth_token']: self.get_contacts()

    def get_access_tokens(self):
        client = oauth.Client(self.consumer)
        request_token_url = 'https://api.linkedin.com/uas/oauth/requestToken'
        resp, content = client.request(request_token_url, "POST")
        if resp['status'] != '200':
            raise Exception(self.error('Error: Invalid Response %s.' % resp['status']))
        request_token = dict(urlparse.parse_qsl(content))
        base_authorize_url = 'https://api.linkedin.com/uas/oauth/authorize'
        authorize_url = "%s?oauth_token=%s" % (base_authorize_url, request_token['oauth_token'])
        print "[*] Go to the following link in your browser and enter the pin below:" 
        print authorize_url
        w = webbrowser.get()
        w.open(authorize_url)
        oauth_verifier = ''
        try: oauth_verifier = raw_input('Enter PIN: ')
        except KeyboardInterrupt: sys.stdout.write('\n')
        if not oauth_verifier: return None
        access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'
        token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self.consumer, token)
        resp, content = client.request(access_token_url, "POST")
        self.access_token = dict(urlparse.parse_qsl(content))
        self.add_key_to_file('linkedin_token', self.access_token['oauth_token'])
        self.add_key_to_file('linkedin_token_secret', self.access_token['oauth_token_secret'])
    
    def get_contacts(self):
        if not hasattr(self, 'access_token'): return
        # Use developer token and secret to instantiate access token object
        token = oauth.Token(key=self.access_token['oauth_token'], secret=self.access_token['oauth_token_secret'])
        client = oauth.Client(self.consumer, token)
        count = 25
        base_url = "http://api.linkedin.com/v1/people-search:(people:(id,first-name,last-name,headline))?format=json&company-name=%s&current-company=true&count=%d" % (urllib.quote_plus(self.options['company']), count)
        url = base_url
        page = 1
        while True:
            # Make call to LinkedIn to retrieve your own profile
            resp,content = client.request(url)
            #import pdb;pdb.set_trace()
            try: jsonobj = json.loads(content)
            except ValueError as e:
                self.error('Error: %s in %s' % (e, url))
                continue
            if resp['status'] == '401':
                self.error('Access Token Needed or Expired.')
                self.get_access_tokens()
                self.get_contacts()
                break
            elif resp['status'] == '403':
                self.error('Error accessing API: %s' % jsonobj['message'])
                break
            if not 'values' in jsonobj['people']: break
            for contact in jsonobj['people']['values']:
                if 'headline' in contact:
                    title = self.unescape(contact['headline'])
                    fname = self.unescape(re.split('[\s]',contact['firstName'])[0])
                    lname = self.unescape(re.split('[,;]',contact['lastName'])[0])
                    print '[Contact] %s %s - %s' % (fname, lname, title)
                    self.add_contact(fname, lname, title)
            if not '_start' in jsonobj['people']: break
            if jsonobj['people']['_start'] + jsonobj['people']['_count'] == jsonobj['people']['_total']: break
            start = page * jsonobj['people']['_count']
            url = '%s&start=%d' % (base_url, start)
            page += 1