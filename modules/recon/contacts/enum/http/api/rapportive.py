import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of accounts for module input (see \'info\' for options)')
        self.register_option('company', self.global_options['company'], 'yes', self.global_options.description['company'])
        self.info = {
            'Name': 'Rapportive Contact Enumerator',
            'Author': 'Quentin Kaiser (@qkaiser, contact[at]quentinkaiser.be) and Tim Tomes (@LaNMaSteR53)',
            'Description': 'Harvests contact information from the Rapportive.com API and updates the \'contacts\' table of the database with the results.',
            'Comments': []
        }

    def get_rapportive_session_token(self):
        token_name = 'rapportive_token'
        try:
            return self.get_key(token_name)
        except:
            pass
        resp = self.request('https://rapportive.com/login_status?user_email=%s@mail.com' % (self.random_str(15)))
        if 'error' in resp.json:
            raise framework.FrameworkException(resp.json['error'])
        session_token = resp.json['session_token']
        self.add_key(token_name, session_token)
        return session_token

    def module_run(self):

        emails = self.get_source(self.options['source'], "SELECT DISTINCT email FROM contacts ORDER BY email")
        session_token = self.get_rapportive_session_token()
        headers = {'X-Session-Token' : session_token}
        cnt = 0
        new = 0
        email = emails.pop(0)

        while True:
            resp = self.request('https://profiles.rapportive.com/contacts/email/%s' % (email), headers=headers)
            if resp.status_code == 403:
                # renew token
                self.output('Renewing expired session token...')
                self.delete_key('rapportive_token')
                session_token = self.get_rapportive_session_token()
                headers = {'X-Session-Token' : session_token}
            elif resp.status_code == 200:
                contact = resp.json['contact']
                last_name = contact['last_name']
                first_name = contact['first_name']
                if any((first_name, last_name)):
                    cnt += 1
                    self.output('%s => %s %s' % (email, first_name, last_name))
                    region = contact['location']
                    self.output('%s %s - %s' % (first_name, last_name, region))
                    for occupation in contact['occupations']:
                        job_title = occupation['job_title']
                        company = occupation['company']
                        if self.options['company'].lower() in company.lower():
                            method = getattr(self, 'alert')
                            new += self.add_contact(first_name, last_name, job_title, email, region)
                        else:
                            method = getattr(self, 'output')
                        method('%s %s - %s at %s' % (first_name, last_name, job_title, company))
                    for membership in contact['memberships']:
                        site = membership['site_name']
                        profile = membership['profile_url']
                        self.output('%s %s - %s (%s)' % (first_name, last_name, site, profile))
                else:
                    self.verbose('%s => Not found.' % (email))
            else:
                self.error('Error: %s' % (resp.json['error_code']))
            if not emails: break
            email = emails.pop(0)

        self.output('Information found for %d emails.' % (cnt))
        if new: self.alert('NEW information found for %d contacts!' % (new))
