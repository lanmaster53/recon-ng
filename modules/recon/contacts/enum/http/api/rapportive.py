import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of accounts for module input (see \'info\' for options)')
        self.register_option('company', self.goptions['company']['value'], 'yes', self.goptions['company']['desc'])
        self.info = {
            'Name': 'Rapportive Contact Enumerator',
            'Author': 'Quentin Kaiser (@qkaiser, contact[at]quentinkaiser.be)',
            'Description': 'Harvests contact information from the Rapportive.com API and updates the \'contacts\' table of the database with the results.',
            'Comments': []
        }

    def module_run(self):

        resp = self.request('https://rapportive.com/login_status?user_email=%s@mail.com' % (self.random_str(15)))

        if resp.status_code == 200 and 'session_token' in resp.json:
            session_token = resp.json['session_token']
            emails = self.get_source(self.options['source']['value'], "SELECT DISTINCT email FROM contacts ORDER BY email")
            new = 0
            for email in emails:
                new += self.call_api(session_token, email)
            if new: self.alert('NEW information found for %d contacts!' % (new))
        else:
            self.error('Error: %s' % (resp.json['error']))

    def call_api(self, session_token, email):

        headers = {'X-Session-Token' : session_token}
        resp = self.request('https://profiles.rapportive.com/contacts/email/%s' % (email), headers=headers)
        found = 0
        if resp.status_code == 200 and 'contact' in resp.json:
            contact = resp.json['contact']
            last_name = contact['last_name']
            first_name = contact['first_name']
            if any((first_name, last_name)):
                self.output('%s => %s %s' % (email, first_name, last_name))
                region = contact['location']
                self.output('%s %s - %s' % (first_name, last_name, region))
                for occupation in contact['occupations']:
                    job_title = occupation['job_title']
                    company = occupation['company']
                    if self.options['company']['value'].lower() in company.lower():
                        self.alert('%s %s - %s at %s' % (first_name, last_name, job_title, company))
                        found = self.add_contact(first_name, last_name, job_title, email, region)
                    else:
                        self.output('%s %s - %s at %s' % (first_name, last_name, job_title, company))
                for membership in contact['memberships']:
                    site = membership['site_name']
                    profile = membership['profile_url']
                    self.output('%s %s - %s (%s)' % (first_name, last_name, site, profile))
            else:
                self.verbose('%s => Not found.' % (email))
        else:
            self.error('Error: %s' % (resp.json['error_code']))

        return found
