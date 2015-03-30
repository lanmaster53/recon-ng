from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'FullContact Contact Enumerator',
        'author': 'Quentin Kaiser (@qkaiser, contact[at]quentinkaiser.be) and Tim Tomes (@LaNMaSteR53)',
        'description': 'Harvests contact information and profiles from the fullcontact.com API using email addresses as input. Updates the \'contacts\' and \'profiles\' tables with the results.',
        'query': 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL',
    }

    def module_run(self, emails):
        key = self.get_key('fullcontact_api')
        url = 'https://api.fullcontact.com/v2/person.json'
        for email in emails:
            payload = {'email':email, 'apiKey':key}
            resp = self.request(url, payload=payload)
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
                            if occupation['current']:
                                title = '%s at %s' % (occupation['title'], occupation['name'])
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
                        username = profile['username']
                        resource = profile['typeName']
                        url = profile['url']
                        self.add_profiles(username=username, url=url, resource=resource, category='social')
                        self.alert('%s - %s (%s)' % (username, resource, url))
                self.output('Confidence: %d%%' % (resp.json['likelihood']*100,))
            else:
                self.output(resp.json['message'])
