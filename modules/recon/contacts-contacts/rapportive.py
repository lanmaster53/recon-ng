import module
# unique to module
import urllib
import re

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')
        self.info = {
                     'Name': 'Rapportive Contact Enumerator',
                     'Author': 'Quentin Kaiser (@qkaiser, contact[at]quentinkaiser.be) and Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Harvests contact information from the Rapportive.com API using email addresses as input. Updates the \'contacts\' table with the results.',
                     'Comments': [
                                  'This module only stores contacts whose company matches an entry in the companies table.'
                                  ]
                     }

    def get_rapportive_session_token(self):
        token_name = 'rapportive_token'
        try:
            return self.get_key(token_name)
        except:
            pass
        resp = self.request('https://rapportive.com/login_status?user_email=%s@mail.com' % (self.random_str(15)))
        if 'error' in resp.json:
            self.error(resp.json['error'])
            return None
        session_token = resp.json['session_token']
        self.add_key(token_name, session_token)
        return session_token

    def module_run(self, emails):
        session_token = self.get_rapportive_session_token()
        # normally handled as a FrameworkException, but needed here due to how the session token is retrieved
        if session_token is None: return
        headers = {'X-Session-Token' : session_token}
        # build a regex that matches any of the stored companies
        companies = [x[0] for x in self.query('SELECT DISTINCT company from companies WHERE company IS NOT NULL')]
        regex = '(?:%s)' % ('|'.join([re.escape(x) for x in companies]))
        cnt = 0
        new = 0
        email = emails.pop(0)

        # must use "while" rather than "for" loop to prevent iterating upon session expiration
        while True:
            resp = self.request('https://profiles.rapportive.com/contacts/email/%s' % (urllib.quote_plus(email.encode('utf-8'))), headers=headers)
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
                        if re.search(regex, company, re.IGNORECASE):
                            method = getattr(self, 'alert')
                            new += self.add_contacts(first_name, last_name, job_title, email=email, region=region)
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
        self.summarize(new, cnt)
