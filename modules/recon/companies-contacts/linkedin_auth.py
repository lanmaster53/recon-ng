from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'LinkedIn Authenticated Contact Enumerator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Harvests contacts from the LinkedIn.com API using an authenticated connections network. Updates the \'contacts\' table with the results.',
        'required_keys': ['linkedin_api', 'linkedin_secret'],
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL',
    }

    def get_linkedin_access_token(self):
        return self.get_explicit_oauth_token(
            'linkedin',
            'r_basicprofile r_network',
            'https://www.linkedin.com/uas/oauth2/authorization',
            'https://www.linkedin.com/uas/oauth2/accessToken'
        )

    def module_run(self, companies):
        access_token = self.get_linkedin_access_token()
        if access_token is None: return
        count = 25
        url = 'https://api.linkedin.com/v1/people-search:(people:(id,first-name,last-name,headline,location:(name,country:(code))))'
        for company in companies:
            self.heading(company, level=0)
            payload = {'format': 'json', 'company-name': company, 'current-company': 'true', 'count': count, 'oauth2_access_token': access_token}
            page = 1
            while True:
                resp = self.request(url, payload=payload)
                jsonobj = resp.json
                # check for an erroneous request
                if 'errorCode' in jsonobj:
                    # check for an expired access token
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
                    # the headline field does not exist when a connection is private
                    # only public connections can be harvested beyond the 1st degree
                    if 'headline' in contact:
                        fname = self.html_unescape(re.split('[\s]',contact['firstName'])[0])
                        lname = self.html_unescape(re.split('[,;]',contact['lastName'])[0])
                        title = self.html_unescape(contact['headline'])
                        region = re.sub('(?:Greater\s|\sArea)', '', self.html_unescape(contact['location']['name']).title())
                        country = self.html_unescape(contact['location']['country']['code']).upper()
                        self.add_contacts(first_name=fname, last_name=lname, title=title, region=region, country=country)
                if not '_start' in jsonobj['people']:
                    break
                if jsonobj['people']['_start'] + jsonobj['people']['_count'] == jsonobj['people']['_total']:
                    break
                payload['start'] = page * jsonobj['people']['_count']
                page += 1
