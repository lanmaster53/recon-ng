import framework
# unique to module
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
        access_token = self.get_linkedin_access_token()
        count = 25
        url = 'https://api.linkedin.com/v1/people-search:(people:(id,first-name,last-name,headline,location:(name,country:(code))))'
        payload = {'format': 'json', 'company-name': self.options['company']['value'], 'current-company': 'true', 'count': count, 'oauth2_access_token': access_token}
        cnt, tot = 0, 0
        page = 1
        while True:
            resp = self.request(url, payload=payload)
            jsonobj = resp.json
            if 'errorCode' in jsonobj:
                if jsonobj['status'] == 401:
                    # renew token
                    self.delete_key('linkedin_token')
                    payload['oauth2_access_token'] = self.get_linkedin_access_token()
                    continue
                self.error(jsonobj['message'])
                break
            if not 'values' in jsonobj['people']:
                break
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
            if not '_start' in jsonobj['people']:
                break
            if jsonobj['people']['_start'] + jsonobj['people']['_count'] == jsonobj['people']['_total']:
                break
            payload['start'] = page * jsonobj['people']['_count']
            page += 1
        self.output('%d total contacts found.' % (tot))
        if cnt: self.alert('%d NEW contacts found!' % (cnt))
