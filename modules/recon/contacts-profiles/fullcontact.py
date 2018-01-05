from recon.core.module import BaseModule
import time

class Module(BaseModule):

    meta = {
        'name': 'FullContact Contact Enumerator',
        'author': 'Quentin Kaiser (@qkaiser, contact[at]quentinkaiser.be) and Tim Tomes (@LaNMaSteR53)',
        'description': 'Harvests contact information and profiles from the fullcontact.com API using email addresses as input. Updates the \'contacts\' and \'profiles\' tables with the results.',
        'required_keys': ['fullcontact_api'],
        'query': 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL',
    }

    def module_run(self, emails):
        api_key = self.keys.get('fullcontact_api')
        base_url = 'https://api.fullcontact.com/v2/person.json'
        while emails:
            email = emails.pop(0)
            payload = {'email':email}
            headers = {'X-FullContact-APIKey': api_key}
            resp = self.request(base_url, payload=payload, headers=headers)
            if resp.status_code == 200:
                # parse contact information
                if 'contactInfo' in resp.json:
                    try:
                        first_name = resp.json['contactInfo']['givenName']
                        last_name = resp.json['contactInfo']['familyName']
                        middle_name = None
                    except KeyError:
                        first_name, middle_name, last_name = self.parse_name(resp.json['contactInfo']['fullName'])
                    name = ' '.join([x for x in (first_name, middle_name, last_name) if x])
                    self.alert('%s - %s' % (name, email))
                    # parse company information for title
                    title = None
                    if 'organizations' in resp.json:
                        for occupation in resp.json['organizations']:
                            if 'current' in occupation and occupation['current']:
                                if 'title' in occupation:
                                    title = '%s at %s' % (occupation['title'], occupation['name'])
                                else:
                                    title = 'Employee at %s' % occupation['name']
                                self.output(title)
                    # parse demographics for region
                    region = None
                    if 'demographics' in resp.json and 'locationGeneral' in resp.json['demographics']:
                        region = resp.json['demographics']['locationGeneral']
                        self.output(region)
                    self.add_contacts(first_name=first_name, middle_name=middle_name, last_name=last_name, title=title, email=email, region=region)
                # parse profile information
                if 'socialProfiles' in resp.json:
                    for profile in resp.json['socialProfiles']:
                        # set the username to 'username' or 'id' and default to email if they are unknown
                        username = email
                        for key in ['username', 'id']:
                            if key in profile:
                                username = profile[key]
                                break
                        resource = profile['typeName']
                        url = profile['url']
                        self.add_profiles(username=username, url=url, resource=resource, category='social')
                self.output('Confidence: %d%%' % (resp.json['likelihood']*100,))
            elif resp.status_code == 202:
                # add emails queued by fullcontact back to the list
                emails.append(email)
                self.output('%s - Queued for search.' % email)
            else:
                self.output('%s - %s' % (email, resp.json['message']))
            # 60 requests per minute api rate limit
            time.sleep(1)
