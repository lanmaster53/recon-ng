import framework
# unique to module
import oauth2 as oauth
import httplib2
import urlparse
import webbrowser
import urllib
import json
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('company', self.goptions['company']['value'], 'yes', self.goptions['company']['desc'])
        self.info = {
                     'Name': 'LinkedIn Authenticated Contact Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests contacts from the LinkedIn.com API using an authenticated connections network and updates the \'contacts\' table of the database with the results.',
                     'Comments': []
                     }

    def module_run(self):
        consumer_key = self.get_key('linkedin_api')
        consumer_secret = self.get_key('linkedin_secret')
        # Use API key and secret to instantiate consumer object
        self.consumer = oauth.Consumer(consumer_key, consumer_secret)
        self.access_token = {}
        try: self.access_token = {'oauth_token': self.get_key('linkedin_token'),'oauth_token_secret': self.get_key('linkedin_token_secret')}
        except framework.FrameworkException: pass
        if not self.access_token: self.get_access_tokens()
        if self.access_token: self.get_contacts()

    def get_access_tokens(self):
        client = oauth.Client(self.consumer)
        request_token_url = 'https://api.linkedin.com/uas/oauth/requestToken?scope=r_basicprofile+r_network'
        resp, content = client.request(request_token_url, "POST")
        if resp['status'] != '200':
            raise Exception(self.error('Error: Invalid Response %s.' % resp['status']))
        request_token = dict(urlparse.parse_qsl(content))
        base_authorize_url = 'https://api.linkedin.com/uas/oauth/authorize'
        authorize_url = "%s?oauth_token=%s" % (base_authorize_url, request_token['oauth_token'])
        self.output('Go to the following link in your browser and enter the pin below:') 
        self.output(authorize_url)
        w = webbrowser.get()
        w.open(authorize_url)
        oauth_verifier = ''
        oauth_verifier = raw_input('Enter PIN: ')
        if not oauth_verifier: return None
        access_token_url = 'https://api.linkedin.com/uas/oauth/accessToken'
        token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self.consumer, token)
        resp, content = client.request(access_token_url, "POST")
        self.access_token = dict(urlparse.parse_qsl(content))
        self.add_key('linkedin_token', self.access_token['oauth_token'])
        self.add_key('linkedin_token_secret', self.access_token['oauth_token_secret'])
    
    def get_contacts(self):
        if not hasattr(self, 'access_token'): return
        # Use developer token and secret to instantiate access token object
        token = oauth.Token(key=self.access_token['oauth_token'], secret=self.access_token['oauth_token_secret'])
        client = oauth.Client(self.consumer, token)
        count = 25
        base_url = "http://api.linkedin.com/v1/people-search:(people:(id,first-name,last-name,headline,location:(name,country:(code))))?format=json&company-name=%s&current-company=true&count=%d" % (urllib.quote_plus(self.options['company']['value']), count)
        url = base_url
        cnt, tot = 0, 0
        page = 1
        while True:
            resp, content = client.request(url)
            jsonstr = content
            try: jsonobj = json.loads(jsonstr)
            except ValueError as e:
                self.error(e.__str__())
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
                    fname = self.html_unescape(re.split('[\s]',contact['firstName'])[0])
                    lname = self.html_unescape(re.split('[,;]',contact['lastName'])[0])
                    title = self.html_unescape(contact['headline'])
                    region = re.sub('(?:Greater\s|\sArea)', '', self.html_unescape(contact['location']['name']).title())
                    country = self.html_unescape(contact['location']['country']['code']).upper()
                    self.output('%s %s - %s (%s - %s)' % (fname, lname, title, region, country))
                    tot += 1
                    cnt += self.add_contact(fname=fname, lname=lname, title=title, region=region, country=country)
            if not '_start' in jsonobj['people']: break
            if jsonobj['people']['_start'] + jsonobj['people']['_count'] == jsonobj['people']['_total']: break
            start = page * jsonobj['people']['_count']
            url = '%s&start=%d' % (base_url, start)
            page += 1
        self.output('%d total contacts found.' % (tot))
        if cnt: self.alert('%d NEW contacts found!' % (cnt))
